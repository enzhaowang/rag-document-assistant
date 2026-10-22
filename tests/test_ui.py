"""Streamlit UI: HTTP client helpers, history building and full-page behaviour.

The backend is faked at the httpx transport level, so these tests need neither a running
API nor OpenAI. Page tests use Streamlit's `AppTest`, which runs the real script.
"""

from __future__ import annotations

import json
from collections.abc import Callable, Iterator
from pathlib import Path
from typing import Any

import httpx
import pytest
from streamlit.testing.v1 import AppTest

from app.config import Settings
from ui import streamlit_app as ui

REPO_ROOT = Path(__file__).resolve().parents[1]
APP_PATH = REPO_ROOT / "ui" / "streamlit_app.py"

Handler = Callable[[httpx.Request], httpx.Response]

SOURCE = {
    "document": "Product Guide - Lumora Thermostat T2.pdf",
    "page": 7,
    "section": "7.1 Warranty",
    "snippet": "The Thermostat T2 has a 2-year (24-month) limited warranty.",
    "score": 0.8123,
    "chunk_id": "product-guide-lumora-thermostat-t2__p7__c0",
}


def chat_body(answer: str = "The T2 has a 2-year warranty.", **overrides: Any) -> dict[str, Any]:
    body: dict[str, Any] = {
        "answer": answer,
        "is_answerable": True,
        "sources": [SOURCE],
        "model": "gpt-4o-mini",
        "latency_ms": 1234,
    }
    body.update(overrides)
    return body


HEALTH_OK = {"status": "ok", "collection": "company_docs", "chunk_count": 245, "document_count": 12}


class FakeBackend:
    """Answers /health and /chat like the API and records every /chat request body."""

    def __init__(
        self,
        chat: Handler | None = None,
        health: Handler | None = None,
    ) -> None:
        self.chat_requests: list[dict[str, Any]] = []
        self._chat = chat or (lambda request: httpx.Response(200, json=chat_body()))
        self._health = health or (lambda request: httpx.Response(200, json=HEALTH_OK))

    def __call__(self, request: httpx.Request) -> httpx.Response:
        if request.url.path == "/health":
            return self._health(request)
        if request.url.path == "/chat":
            self.chat_requests.append(json.loads(request.content))
            return self._chat(request)
        return httpx.Response(404, json={"detail": "Not Found"})


def _client(handler: Handler) -> httpx.Client:
    return ui.make_client(ui.UISettings(_env_file=None), transport=httpx.MockTransport(handler))


def _raise(exc: Exception) -> Handler:
    def handler(request: httpx.Request) -> httpx.Response:
        raise exc

    return handler


# --------------------------------------------------------------------------- settings


def test_ui_settings_match_backend_settings() -> None:
    backend = Settings(_env_file=None)
    ui_settings = ui.UISettings(_env_file=None)

    for name in ui.UISettings.model_fields:
        assert name in Settings.model_fields, f"{name} missing from app Settings/.env.example"
        assert getattr(ui_settings, name) == getattr(backend, name)


def test_ui_does_not_import_backend_code() -> None:
    source = APP_PATH.read_text()

    assert "from app" not in source
    assert "import app" not in source


# --------------------------------------------------------------------------- HTTP helpers


def test_client_uses_api_base_url_and_ignores_proxies(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HTTP_PROXY", "http://127.0.0.1:9")

    with ui.make_client(ui.UISettings(_env_file=None, api_base_url="http://api:8080/")) as client:
        assert str(client.base_url) == "http://api:8080"
        assert client.trust_env is False


def test_send_chat_returns_response_and_posts_contract_body() -> None:
    backend = FakeBackend()
    history = [{"role": "user", "content": "Hi"}, {"role": "assistant", "content": "Hello"}]

    with _client(backend) as client:
        outcome = ui.send_chat(client, "How long is the T2 warranty?", history)

    assert outcome.error is None
    assert outcome.response == chat_body()
    assert backend.chat_requests == [
        {"question": "How long is the T2 warranty?", "history": history}
    ]


@pytest.mark.parametrize(
    ("handler", "expected"),
    [
        (_raise(httpx.ConnectError("refused")), "Cannot reach the assistant backend"),
        (_raise(httpx.ReadTimeout("slow")), ui.MSG_BACKEND_TIMEOUT),
        (_raise(httpx.ConnectTimeout("no route")), "Cannot reach the assistant backend"),
        (
            lambda r: httpx.Response(503, json={"detail": "The model is busy.", "request_id": "x"}),
            "The model is busy.",
        ),
        (lambda r: httpx.Response(500, text="<html>oops</html>"), "HTTP 500"),
        (lambda r: httpx.Response(422, json={"detail": [{"msg": "bad"}]}), ui.MSG_INVALID_QUESTION),
        (lambda r: httpx.Response(200, text="not json"), ui.MSG_BAD_RESPONSE),
        (lambda r: httpx.Response(200, json={"answer": "x"}), ui.MSG_BAD_RESPONSE),
    ],
)
def test_send_chat_turns_failures_into_friendly_errors(handler: Handler, expected: str) -> None:
    with _client(handler) as client:
        outcome = ui.send_chat(client, "question", [])

    assert outcome.response is None
    assert outcome.error is not None
    assert expected in outcome.error
    assert "Traceback" not in outcome.error


def test_send_chat_keeps_request_id_of_errors() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(503, json={"detail": "Busy."}, headers={"X-Request-ID": "abc123"})

    with _client(handler) as client:
        outcome = ui.send_chat(client, "question", [])

    assert outcome.request_id == "abc123"


def test_fetch_health_states() -> None:
    with _client(FakeBackend()) as client:
        ok = ui.fetch_health(client)
    assert (ok.reachable, ok.healthy, ok.document_count, ok.chunk_count) == (True, True, 12, 245)

    degraded_body = {"status": "unavailable", "collection": "c", "detail": "Chroma is down."}
    with _client(lambda r: httpx.Response(503, json=degraded_body)) as client:
        degraded = ui.fetch_health(client)
    assert (degraded.reachable, degraded.healthy, degraded.detail) == (
        True,
        False,
        "Chroma is down.",
    )

    with _client(_raise(httpx.ConnectError("refused"))) as client:
        down = ui.fetch_health(client)
    assert (down.reachable, down.healthy) == (False, False)


# --------------------------------------------------------------------------- history


def test_build_history_keeps_completed_turns_only() -> None:
    messages = [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1", "is_answerable": True},
        {"role": "user", "content": "q2 (failed)"},
        {"role": "assistant", "content": "Cannot reach the backend", "error": True},
        {"role": "user", "content": "q3"},
        {"role": "assistant", "content": "refused", "is_answerable": False},
    ]

    assert ui.build_history(messages, max_turns=6) == [
        {"role": "user", "content": "q1"},
        {"role": "assistant", "content": "a1"},
        {"role": "user", "content": "q3"},
        {"role": "assistant", "content": "refused"},
    ]


def test_build_history_limits_turns_and_message_length() -> None:
    messages: list[dict[str, Any]] = []
    for i in range(10):
        messages += [
            {"role": "user", "content": f"q{i}"},
            {"role": "assistant", "content": f"a{i}" + "x" * 9000},
        ]

    history = ui.build_history(messages, max_turns=2)

    assert [m["content"][:2] for m in history] == ["q8", "a8", "q9", "a9"]
    assert all(len(m["content"]) <= ui.HISTORY_MESSAGE_MAX_CHARS for m in history)
    assert ui.build_history(messages, max_turns=0) == []


def test_source_label_and_score_formatting() -> None:
    assert ui.source_label(SOURCE) == (
        "Product Guide - Lumora Thermostat T2.pdf · Page 7 · 7.1 Warranty"
    )
    assert ui.source_label({"document": "FAQ.pdf", "page": 2, "section": None}) == (
        "FAQ.pdf · Page 2"
    )
    assert ui.format_score(0.8123) == "0.81"
    assert ui.format_score(None) == "n/a"


def test_escape_markdown_math_escapes_dollars_once() -> None:
    assert ui.escape_markdown_math("$250.01 to $1,000.00") == r"\$250.01 to \$1,000.00"
    assert ui.escape_markdown_math(r"already \$5") == r"already \$5"
    assert ui.escape_markdown_math("no amounts") == "no amounts"


# --------------------------------------------------------------------------- full page


@pytest.fixture
def fake_backend(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> Iterator[Callable[..., FakeBackend]]:
    """Route every real httpx request made by the page to a `FakeBackend`."""

    def install(**kwargs: Any) -> FakeBackend:
        backend = FakeBackend(**kwargs)
        monkeypatch.setattr(
            httpx.HTTPTransport, "handle_request", lambda self, request: backend(request)
        )
        return backend

    yield install


def _app() -> AppTest:
    return AppTest.from_file(str(APP_PATH), default_timeout=10)


def test_page_renders_health_in_sidebar(fake_backend: Callable[..., FakeBackend]) -> None:
    fake_backend()

    at = _app().run()

    assert not at.exception
    assert at.title[0].value == ui.APP_TITLE
    assert [m.value for m in at.sidebar.metric] == ["12", "245"]
    assert at.sidebar.success[0].value == "Connected"


def test_multi_turn_conversation_sends_history_and_shows_sources(
    fake_backend: Callable[..., FakeBackend],
) -> None:
    answers = iter(
        [
            chat_body("The T2 has a 2-year warranty."),
            chat_body(
                "The T3 has a 3-year warranty.",
                sources=[{**SOURCE, "document": "Product Guide - Lumora Thermostat T3.pdf"}],
            ),
        ]
    )
    backend = fake_backend(chat=lambda request: httpx.Response(200, json=next(answers)))

    at = _app().run()
    at.chat_input[0].set_value("How long is the T2 warranty?").run()
    at.chat_input[0].set_value("And the T3?").run()

    assert not at.exception
    assert backend.chat_requests == [
        {"question": "How long is the T2 warranty?", "history": []},
        {
            "question": "And the T3?",
            "history": [
                {"role": "user", "content": "How long is the T2 warranty?"},
                {"role": "assistant", "content": "The T2 has a 2-year warranty."},
            ],
        },
    ]
    assert [m.name for m in at.chat_message] == ["user", "assistant", "user", "assistant"]
    labels = [e.label for e in at.expander]
    assert labels == [
        "Product Guide - Lumora Thermostat T2.pdf · Page 7 · 7.1 Warranty",
        "Product Guide - Lumora Thermostat T3.pdf · Page 7 · 7.1 Warranty",
    ]
    assert "Relevance score: 0.81" in [c.value for c in at.expander[0].caption]
    assert "gpt-4o-mini · 1.2 s" in [c.value for c in at.caption]


def test_refusal_is_shown_as_warning(fake_backend: Callable[..., FakeBackend]) -> None:
    refusal = "I'm sorry, I couldn't find this information in the available documents."
    fake_backend(
        chat=lambda r: httpx.Response(200, json=chat_body(refusal, is_answerable=False, sources=[]))
    )

    at = _app().run()
    at.chat_input[0].set_value("Who is the CEO?").run()

    assert not at.exception
    assert [w.value for w in at.main.warning] == [refusal]
    assert len(at.expander) == 0


def test_example_question_button_asks_it(fake_backend: Callable[..., FakeBackend]) -> None:
    backend = fake_backend()

    at = _app().run()
    at.button(key="example_0").click().run()

    assert not at.exception
    assert backend.chat_requests[0]["question"] == ui.EXAMPLE_QUESTIONS[0]
    assert at.chat_message[0].markdown[0].value == ui.EXAMPLE_QUESTIONS[0]


def test_clear_conversation_button(fake_backend: Callable[..., FakeBackend]) -> None:
    fake_backend()

    at = _app().run()
    at.chat_input[0].set_value("How long is the T2 warranty?").run()
    assert len(at.chat_message) == 2

    clear = next(b for b in at.sidebar.button if b.label == "Clear conversation")
    clear.click().run()

    assert not at.exception
    assert len(at.chat_message) == 0
    assert at.session_state.messages == []


def test_backend_down_shows_friendly_errors_without_crashing(
    fake_backend: Callable[..., FakeBackend],
) -> None:
    down = _raise(httpx.ConnectError("connection refused"))
    backend = fake_backend(chat=down, health=down)

    at = _app().run()
    assert not at.exception
    assert "Backend unreachable" in at.sidebar.error[0].value

    at.chat_input[0].set_value("How long is the T2 warranty?").run()

    assert not at.exception
    assert "Cannot reach the assistant backend" in at.main.error[0].value
    assert len(backend.chat_requests) == 1

    # The failed turn is not sent as history once the backend is back.
    backend._chat = lambda request: httpx.Response(200, json=chat_body())
    at.chat_input[0].set_value("Second try").run()
    assert backend.chat_requests[-1] == {"question": "Second try", "history": []}


def test_dollar_amounts_are_escaped_for_display_but_history_keeps_raw_text(
    fake_backend: Callable[..., FakeBackend],
) -> None:
    answer = "Refunds of $250.01 to $1,000.00 need a Team Lead; $1,000.01 to $5,000.00 a Manager."
    snippet = "4.1 Refund Approval Thresholds: $250.01 to $1,000.00 - Team Lead."
    refusal = "I could not find who approves refunds above $5,000 or below $10."
    answers = iter(
        [
            chat_body(answer, sources=[{**SOURCE, "snippet": snippet}]),
            chat_body(refusal, is_answerable=False, sources=[]),
        ]
    )
    backend = fake_backend(chat=lambda request: httpx.Response(200, json=next(answers)))

    at = _app().run()
    at.chat_input[0].set_value("Who approves $800 or $3,000?").run()
    at.chat_input[0].set_value("And above $5,000?").run()

    assert not at.exception
    first_user, first_answer = at.chat_message[0], at.chat_message[1]
    assert first_user.markdown[0].value == r"Who approves \$800 or \$3,000?"
    assert first_answer.markdown[0].value == answer.replace("$", r"\$")
    assert at.expander[0].markdown[0].value == "> " + snippet.replace("$", r"\$")
    assert [w.value for w in at.main.warning] == [refusal.replace("$", r"\$")]
    # The session and the history sent to the API keep the original text.
    assert at.session_state.messages[1]["content"] == answer
    assert backend.chat_requests[1]["history"] == [
        {"role": "user", "content": "Who approves $800 or $3,000?"},
        {"role": "assistant", "content": answer},
    ]
