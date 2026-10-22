"""Streamlit chat UI for the Lumora internal support assistant.

Run with ``make ui`` (or ``streamlit run ui/streamlit_app.py``) while the API is running.

The UI talks to the backend over HTTP only (``POST /chat`` and ``GET /health`` on
API_BASE_URL) and never imports backend code, so it can be deployed as a separate
service. Its few settings are read from the environment / ``.env`` by `UISettings`.

Every backend failure (API down, timeout, error response, malformed body) is turned into
a friendly message shown in the chat; the page itself never crashes.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
import streamlit as st
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

APP_TITLE = "Lumora Support Assistant"
APP_DESCRIPTION = (
    "Ask questions about Lumora product guides, SOPs, FAQs and policies. Every answer "
    "cites the document and page it comes from; questions the documents do not cover "
    "are declined instead of guessed."
)
DEMO_NOTE = "Demo with a fictional company (Lumora Home Systems) and generated sample documents."

# Mirrors the API contract: questions are limited to 2000 characters.
QUESTION_MAX_CHARS = 2000
# The API rejects history messages longer than this; longer answers are trimmed.
HISTORY_MESSAGE_MAX_CHARS = 8000
# /health must answer quickly; a slow health check should not block the page.
HEALTH_TIMEOUT_SECONDS = 5.0

EXAMPLE_QUESTIONS = (
    "How long is the warranty on the Lumora Thermostat T2?",
    "What does error E4 mean on the Thermostat T3?",
    "Who must approve a refund of $800?",
    "Who is the CEO of Lumora?",
)

MSG_BACKEND_UNREACHABLE = (
    "Cannot reach the assistant backend at {url}. Please check that the API is running "
    "and try again."
)
MSG_BACKEND_TIMEOUT = "The assistant backend did not answer in time. Please try again in a moment."
MSG_BACKEND_ERROR = "The assistant backend returned an error (HTTP {status}). Please try again."
MSG_BAD_RESPONSE = "The assistant backend sent an unexpected response. Please try again later."
MSG_INVALID_QUESTION = "The question could not be processed. Please rephrase it and try again."


class UISettings(BaseSettings):
    """UI configuration; field names match the backend Settings (same `.env` file)."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    api_base_url: str = "http://localhost:8080"
    ui_request_timeout_seconds: float = Field(default=120.0, gt=0)
    # Only this many recent turns (user + assistant message) are sent as history.
    rag_history_max_turns: int = Field(default=6, ge=0)


# --------------------------------------------------------------------------- HTTP client


@dataclass
class HealthInfo:
    """Result of `GET /health` as shown in the sidebar."""

    reachable: bool  # the API answered at all
    healthy: bool  # the API reports that the vector store is available
    document_count: int | None = None
    chunk_count: int | None = None
    detail: str | None = None


@dataclass
class ChatOutcome:
    """Result of `POST /chat`: either a response body or a friendly error message."""

    response: dict[str, Any] | None = None
    error: str | None = None
    request_id: str | None = None


def make_client(settings: UISettings, transport: httpx.BaseTransport | None = None) -> httpx.Client:
    """HTTP client for the backend (`transport` lets tests plug in a mock).

    The API is our own service, so proxy settings from the environment or the OS are
    ignored (`trust_env=False`): a desktop proxy without a localhost exception would
    otherwise swallow every request to http://localhost:8080.
    """
    return httpx.Client(
        trust_env=False,
        base_url=settings.api_base_url.rstrip("/"),
        timeout=httpx.Timeout(settings.ui_request_timeout_seconds, connect=HEALTH_TIMEOUT_SECONDS),
        transport=transport,
    )


def _json_body(response: httpx.Response) -> dict[str, Any] | None:
    try:
        body = response.json()
    except ValueError:
        return None
    return body if isinstance(body, dict) else None


def fetch_health(client: httpx.Client) -> HealthInfo:
    """Call `GET /health`; never raises."""
    try:
        response = client.get("/health", timeout=HEALTH_TIMEOUT_SECONDS)
    except httpx.HTTPError:
        return HealthInfo(reachable=False, healthy=False, detail="The API is not reachable.")
    body = _json_body(response) or {}
    if response.status_code == 200 and body.get("status") == "ok":
        return HealthInfo(
            reachable=True,
            healthy=True,
            document_count=body.get("document_count"),
            chunk_count=body.get("chunk_count"),
        )
    detail = body.get("detail") or f"Health check failed (HTTP {response.status_code})."
    return HealthInfo(reachable=True, healthy=False, detail=str(detail))


def _is_valid_chat_body(body: dict[str, Any] | None) -> bool:
    if body is None:
        return False
    return (
        isinstance(body.get("answer"), str)
        and isinstance(body.get("is_answerable"), bool)
        and isinstance(body.get("sources"), list)
        and all(isinstance(source, dict) for source in body["sources"])
    )


def send_chat(client: httpx.Client, question: str, history: list[dict[str, str]]) -> ChatOutcome:
    """Call `POST /chat`; never raises. Errors become a user-facing message."""
    try:
        response = client.post("/chat", json={"question": question, "history": history})
    except httpx.TimeoutException:
        return ChatOutcome(error=MSG_BACKEND_TIMEOUT)
    except httpx.HTTPError:
        return ChatOutcome(error=MSG_BACKEND_UNREACHABLE.format(url=client.base_url))

    body = _json_body(response)
    request_id = response.headers.get("X-Request-ID")
    if response.status_code == 200:
        if not _is_valid_chat_body(body):
            return ChatOutcome(error=MSG_BAD_RESPONSE, request_id=request_id)
        return ChatOutcome(response=body, request_id=request_id)
    if response.status_code == 422:
        return ChatOutcome(error=MSG_INVALID_QUESTION, request_id=request_id)
    # The API's error bodies carry a friendly `detail` string (e.g. LLM timeouts -> 503).
    detail = body.get("detail") if body else None
    if isinstance(detail, str) and detail.strip():
        return ChatOutcome(error=detail, request_id=request_id)
    return ChatOutcome(
        error=MSG_BACKEND_ERROR.format(status=response.status_code), request_id=request_id
    )


# --------------------------------------------------------------------------- chat state


def build_history(messages: list[dict[str, Any]], max_turns: int) -> list[dict[str, str]]:
    """Turn the displayed conversation into the API `history` (oldest first).

    Only completed turns are sent: a user question whose request failed (and the error
    shown for it) is left out, so the backend never sees error text as an answer. The
    result keeps the last `max_turns` turns.
    """
    turns: list[tuple[str, str]] = []
    pending_question: str | None = None
    for message in messages:
        if message["role"] == "user":
            pending_question = message["content"]
        elif pending_question is not None and not message.get("error"):
            turns.append((pending_question, message["content"]))
            pending_question = None
        else:
            pending_question = None
    if max_turns <= 0:
        return []
    history: list[dict[str, str]] = []
    for question, answer in turns[-max_turns:]:
        history.append({"role": "user", "content": question[:HISTORY_MESSAGE_MAX_CHARS]})
        history.append({"role": "assistant", "content": answer[:HISTORY_MESSAGE_MAX_CHARS]})
    return history


def assistant_message(outcome: ChatOutcome) -> dict[str, Any]:
    """Message stored in the session for one backend outcome."""
    if outcome.response is None:
        return {
            "role": "assistant",
            "content": outcome.error or MSG_BAD_RESPONSE,
            "error": True,
            "request_id": outcome.request_id,
        }
    body = outcome.response
    return {
        "role": "assistant",
        "content": body["answer"],
        "is_answerable": body["is_answerable"],
        "sources": body["sources"],
        "model": body.get("model"),
        "latency_ms": body.get("latency_ms"),
    }


def source_label(source: dict[str, Any]) -> str:
    """One-line citation, e.g. ``SOP - Returns and Refunds.pdf · Page 3 · 4.2 Refunds``."""
    parts = [str(source.get("document") or "Unknown document")]
    if source.get("page") is not None:
        parts.append(f"Page {source['page']}")
    if source.get("section"):
        parts.append(str(source["section"]))
    return " · ".join(parts)


def format_score(score: Any) -> str:
    try:
        return f"{float(score):.2f}"
    except (TypeError, ValueError):
        return "n/a"


# --------------------------------------------------------------------------- rendering


def render_sources(sources: list[dict[str, Any]]) -> None:
    if not sources:
        return
    st.markdown("**Sources**")
    for source in sources:
        with st.expander(source_label(source), icon=":material/description:"):
            st.caption(f"Relevance score: {format_score(source.get('score'))}")
            snippet = str(source.get("snippet") or "").strip()
            if snippet:
                st.markdown("> " + snippet.replace("\n", "\n> "))


def render_message(message: dict[str, Any]) -> None:
    """Draw one stored message inside its chat bubble."""
    if message["role"] == "user":
        st.markdown(message["content"])
        return
    if message.get("error"):
        st.error(message["content"], icon=":material/error:")
        if message.get("request_id"):
            st.caption(f"Request ID: {message['request_id']}")
        return
    if message.get("is_answerable"):
        st.markdown(message["content"])
    else:
        # Refusals look different so they are never mistaken for an answer.
        st.warning(message["content"], icon=":material/info:")
    render_sources(message.get("sources") or [])
    meta = []
    if message.get("model"):
        meta.append(str(message["model"]))
    if isinstance(message.get("latency_ms"), int | float):
        meta.append(f"{message['latency_ms'] / 1000:.1f} s")
    if meta:
        st.caption(" · ".join(meta))


def _ask_example(question: str) -> None:
    st.session_state.pending_question = question


def _clear_conversation() -> None:
    st.session_state.messages = []
    st.session_state.pending_question = None


def render_sidebar(health: HealthInfo, settings: UISettings) -> None:
    with st.sidebar:
        st.subheader("Backend")
        if health.healthy:
            st.success("Connected", icon=":material/check_circle:")
            col_docs, col_chunks = st.columns(2)
            col_docs.metric("Documents", health.document_count if health.document_count else 0)
            col_chunks.metric("Chunks", health.chunk_count if health.chunk_count else 0)
            if not health.chunk_count:
                st.info("The index is empty. Run the ingestion first (`make ingest`).")
        elif health.reachable:
            st.warning(health.detail or "The backend is degraded.", icon=":material/warning:")
        else:
            st.error(f"Backend unreachable at {settings.api_base_url}", icon=":material/cloud_off:")
        st.button("Refresh status", icon=":material/refresh:", width="stretch")

        st.subheader("Try an example")
        for index, question in enumerate(EXAMPLE_QUESTIONS):
            st.button(
                question,
                key=f"example_{index}",
                on_click=_ask_example,
                args=(question,),
                width="stretch",
            )

        st.divider()
        st.button(
            "Clear conversation",
            icon=":material/delete:",
            on_click=_clear_conversation,
            width="stretch",
        )
        st.caption(DEMO_NOTE)


def main() -> None:
    st.set_page_config(page_title=APP_TITLE, page_icon=":material/support_agent:")
    settings = UISettings()
    st.session_state.setdefault("messages", [])
    st.session_state.setdefault("pending_question", None)

    with make_client(settings) as client:
        render_sidebar(fetch_health(client), settings)

        st.title(APP_TITLE)
        st.caption(APP_DESCRIPTION)

        messages: list[dict[str, Any]] = st.session_state.messages
        for message in messages:
            with st.chat_message(message["role"]):
                render_message(message)

        typed = st.chat_input("Ask a question about the documents", max_chars=QUESTION_MAX_CHARS)
        question = typed or st.session_state.pending_question
        st.session_state.pending_question = None
        if not question or not question.strip():
            return
        question = question.strip()

        history = build_history(messages, settings.rag_history_max_turns)
        user_message = {"role": "user", "content": question}
        messages.append(user_message)
        with st.chat_message("user"):
            render_message(user_message)
        with st.chat_message("assistant"):
            with st.spinner("Searching the documents..."):
                outcome = send_chat(client, question, history)
            reply = assistant_message(outcome)
            messages.append(reply)
            render_message(reply)


if __name__ == "__main__":
    main()
