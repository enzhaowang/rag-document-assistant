"""RAG chain: rewriting, early refusal, citation validation (LLM and retriever are mocked)."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path
from typing import Any

import pytest
from langchain_core.documents import Document
from langchain_core.messages import AIMessage, BaseMessage

from app.config import Settings
from app.rag import chain as chain_module
from app.rag.chain import answer_question, build_chat_model
from app.rag.prompts import REFUSAL_MESSAGE
from app.rag.schemas import HistoryMessage, LLMAnswer, RefusalReason


def make_chunk(
    chunk_id: str,
    score: float,
    *,
    source: str = "SOP - Returns and Refunds.pdf",
    page: int = 3,
    text: str | None = None,
    section: str | None = "4.2 Refund Approval",
) -> chain_module.RetrievedChunk:
    metadata = {
        "chunk_id": chunk_id,
        "source": source,
        "doc_title": "Returns and Refunds SOP",
        "doc_type": "sop",
        "page": page,
        "chunk_index": 0,
        "doc_hash": "abc",
        "section": section,
    }
    body = text if text is not None else f"Refunds above $500 need manager approval ({chunk_id})."
    return chain_module.RetrievedChunk(
        doc=Document(page_content=body, metadata=metadata), score=score
    )


class FakeLLM:
    """Stands in for ChatOpenAI: records prompts and returns canned outputs."""

    def __init__(
        self, answer: LLMAnswer | dict[str, Any] | None = None, rewrite: str = "rewritten"
    ) -> None:
        self.answer = answer
        self.rewrite = rewrite
        self.rewrite_calls: list[list[BaseMessage]] = []
        self.answer_calls: list[list[BaseMessage]] = []
        self.structured_kwargs: list[dict[str, Any]] = []

    def invoke(self, messages: list[BaseMessage]) -> AIMessage:
        self.rewrite_calls.append(messages)
        return AIMessage(content=self.rewrite)

    def with_structured_output(self, schema: type, **kwargs: Any) -> FakeLLM._Structured:
        assert schema is LLMAnswer
        self.structured_kwargs.append(kwargs)
        return FakeLLM._Structured(self)

    class _Structured:
        def __init__(self, parent: FakeLLM) -> None:
            self.parent = parent

        def invoke(self, messages: list[BaseMessage]) -> Any:
            self.parent.answer_calls.append(messages)
            return self.parent.answer


class ExplodingLLM:
    """Fails the test if the chain touches the LLM at all."""

    def invoke(self, *_: Any, **__: Any) -> Any:
        raise AssertionError("LLM must not be called")

    def with_structured_output(self, *_: Any, **__: Any) -> Any:
        raise AssertionError("LLM must not be called")


@pytest.fixture
def settings(clean_env: Path) -> Settings:
    return Settings(
        _env_file=None,
        retrieval_top_k=6,
        retrieval_score_threshold=0.35,
        rag_max_context_tokens=3000,
        rag_history_max_turns=2,
    )


@pytest.fixture
def fake_retrieve(
    monkeypatch: pytest.MonkeyPatch,
) -> Callable[[list[chain_module.RetrievedChunk]], list[str]]:
    """Patch `retrieve` to return the given chunks; returns the list of queried questions."""

    def install(chunks: list[chain_module.RetrievedChunk]) -> list[str]:
        queries: list[str] = []

        def _retrieve(question: str, k: int | None = None, **_: Any) -> list[Any]:
            queries.append(question)
            return list(chunks)

        monkeypatch.setattr(chain_module, "retrieve", _retrieve)
        return queries

    return install


def test_no_retrieved_chunks_refuses_without_calling_llm(
    settings: Settings, fake_retrieve: Any, monkeypatch: pytest.MonkeyPatch
) -> None:
    fake_retrieve([])
    monkeypatch.setattr(
        chain_module, "build_chat_model", lambda *_: pytest.fail("LLM must not be built")
    )

    result = answer_question("Who is the CEO?", settings=settings)

    assert result.is_answerable is False
    assert result.answer == REFUSAL_MESSAGE
    assert result.sources == []
    assert result.refusal_reason == RefusalReason.NO_RELEVANT_CHUNKS


def test_chunks_below_threshold_refuse_without_calling_llm(
    settings: Settings, fake_retrieve: Any
) -> None:
    fake_retrieve([make_chunk("a__p1__c0", 0.34), make_chunk("a__p2__c0", 0.1)])

    result = answer_question("How do I make pizza?", settings=settings, llm=ExplodingLLM())

    assert result.is_answerable is False
    assert result.answer == REFUSAL_MESSAGE
    assert result.refusal_reason == RefusalReason.NO_RELEVANT_CHUNKS
    assert result.contexts == []


def test_answer_with_valid_citation_builds_sources_from_metadata(
    settings: Settings, fake_retrieve: Any
) -> None:
    chunk = make_chunk("sop-returns__p3__c1", 0.8123456)
    fake_retrieve([chunk])
    llm = FakeLLM(
        LLMAnswer(
            is_answerable=True,
            answer="A manager must approve it.",
            cited_chunk_ids=["sop-returns__p3__c1"],
        )
    )

    result = answer_question("Who approves a $600 refund?", settings=settings, llm=llm)

    assert result.is_answerable is True
    assert result.answer == "A manager must approve it."
    assert result.refusal_reason is None
    assert [s.model_dump() for s in result.sources] == [
        {
            "document": "SOP - Returns and Refunds.pdf",
            "page": 3,
            "section": "4.2 Refund Approval",
            "snippet": chunk.text,
            "score": 0.8123,
            "chunk_id": "sop-returns__p3__c1",
        }
    ]
    assert result.model == settings.openai_chat_model
    assert result.latency_ms >= 0
    assert llm.structured_kwargs == [{"method": "function_calling"}]
    assert llm.rewrite_calls == []  # no history -> no rewrite


def test_context_labels_chunks_with_id_source_and_page(
    settings: Settings, fake_retrieve: Any
) -> None:
    fake_retrieve([make_chunk("faq-shipping__p2__c0", 0.7, source="FAQ - Shipping.pdf", page=2)])
    llm = FakeLLM(LLMAnswer(is_answerable=False, answer="", cited_chunk_ids=[]))

    answer_question("Shipping cost?", settings=settings, llm=llm)

    prompt = llm.answer_calls[0][-1].content
    assert "[faq-shipping__p2__c0] (FAQ - Shipping.pdf, p.2)" in prompt
    assert "Section: 4.2 Refund Approval" in prompt
    assert "Question: Shipping cost?" in prompt


def test_unknown_chunk_ids_are_dropped(settings: Settings, fake_retrieve: Any) -> None:
    fake_retrieve([make_chunk("real__p3__c0", 0.8)])
    llm = FakeLLM(
        LLMAnswer(
            is_answerable=True,
            answer="Answer.",
            cited_chunk_ids=["invented__p9__c0", "real__p3__c0", "another-fake"],
        )
    )

    result = answer_question("q", settings=settings, llm=llm)

    assert result.is_answerable is True
    assert [s.chunk_id for s in result.sources] == ["real__p3__c0"]


def test_chunk_retrieved_but_not_sent_to_llm_cannot_be_cited(
    settings: Settings, fake_retrieve: Any
) -> None:
    # The second chunk is below the threshold, so it is never shown to the model.
    fake_retrieve([make_chunk("shown__p1__c0", 0.8), make_chunk("hidden__p2__c0", 0.2)])
    llm = FakeLLM(LLMAnswer(is_answerable=True, answer="x", cited_chunk_ids=["hidden__p2__c0"]))

    result = answer_question("q", settings=settings, llm=llm)

    assert result.is_answerable is False
    assert result.refusal_reason == RefusalReason.NO_VALID_CITATIONS
    assert result.sources == []


def test_bracketed_chunk_ids_are_normalized(settings: Settings, fake_retrieve: Any) -> None:
    fake_retrieve([make_chunk("real__p3__c0", 0.8)])
    llm = FakeLLM(LLMAnswer(is_answerable=True, answer="x", cited_chunk_ids=[" [real__p3__c0] "]))

    result = answer_question("q", settings=settings, llm=llm)

    assert [s.chunk_id for s in result.sources] == ["real__p3__c0"]


@pytest.mark.parametrize("cited", [[], ["made-up__p1__c0"]])
def test_answerable_without_valid_citations_is_downgraded(
    settings: Settings, fake_retrieve: Any, cited: list[str]
) -> None:
    fake_retrieve([make_chunk("real__p3__c0", 0.8)])
    llm = FakeLLM(LLMAnswer(is_answerable=True, answer="Confident answer.", cited_chunk_ids=cited))

    result = answer_question("q", settings=settings, llm=llm)

    assert result.is_answerable is False
    assert result.answer == REFUSAL_MESSAGE
    assert result.sources == []
    assert result.refusal_reason == RefusalReason.NO_VALID_CITATIONS


def test_answerable_with_empty_answer_is_downgraded(settings: Settings, fake_retrieve: Any) -> None:
    fake_retrieve([make_chunk("real__p3__c0", 0.8)])
    llm = FakeLLM(LLMAnswer(is_answerable=True, answer="  ", cited_chunk_ids=["real__p3__c0"]))

    result = answer_question("q", settings=settings, llm=llm)

    assert result.is_answerable is False
    assert result.refusal_reason == RefusalReason.NO_VALID_CITATIONS


def test_model_refusal_uses_standard_text_and_names_related_documents(
    settings: Settings, fake_retrieve: Any
) -> None:
    fake_retrieve([make_chunk("rma__p2__c0", 0.6, source="SOP - RMA Process.pdf", page=2)])
    llm = FakeLLM(
        LLMAnswer(
            is_answerable=False,
            answer="Some free text the model should not be able to show.",
            cited_chunk_ids=["rma__p2__c0", "invented__p1__c0"],
        )
    )

    result = answer_question("q", settings=settings, llm=llm)

    assert result.is_answerable is False
    assert result.refusal_reason == RefusalReason.MODEL_DECLINED
    assert result.answer.startswith(REFUSAL_MESSAGE)
    assert "SOP - RMA Process.pdf (p. 2)" in result.answer
    assert "invented" not in result.answer
    assert "free text" not in result.answer
    assert result.sources == []


def test_model_refusal_without_related_chunks_is_exact_refusal_text(
    settings: Settings, fake_retrieve: Any
) -> None:
    fake_retrieve([make_chunk("rma__p2__c0", 0.6)])
    llm = FakeLLM(LLMAnswer(is_answerable=False, answer="", cited_chunk_ids=[]))

    result = answer_question("Write me a poem", settings=settings, llm=llm)

    assert result.answer == REFUSAL_MESSAGE
    assert result.is_answerable is False


def test_missing_structured_output_is_refused(settings: Settings, fake_retrieve: Any) -> None:
    fake_retrieve([make_chunk("real__p3__c0", 0.8)])

    result = answer_question("q", settings=settings, llm=FakeLLM(None))

    assert result.is_answerable is False
    assert result.refusal_reason == RefusalReason.INVALID_MODEL_OUTPUT


def test_dict_structured_output_is_validated(settings: Settings, fake_retrieve: Any) -> None:
    fake_retrieve([make_chunk("real__p3__c0", 0.8)])
    llm = FakeLLM({"is_answerable": True, "answer": "x", "cited_chunk_ids": ["real__p3__c0"]})

    result = answer_question("q", settings=settings, llm=llm)

    assert result.is_answerable is True


def test_sources_are_deduplicated_by_document_and_page(
    settings: Settings, fake_retrieve: Any
) -> None:
    fake_retrieve(
        [
            make_chunk("a__p3__c1", 0.9),
            make_chunk("a__p3__c0", 0.7),
            make_chunk("b__p1__c0", 0.6, source="FAQ - Billing.pdf", page=1),
            make_chunk("a__p4__c0", 0.5, page=4),
        ]
    )
    llm = FakeLLM(
        LLMAnswer(
            is_answerable=True,
            answer="x",
            cited_chunk_ids=["a__p3__c0", "b__p1__c0", "a__p3__c1", "a__p4__c0", "a__p3__c0"],
        )
    )

    result = answer_question("q", settings=settings, llm=llm)

    assert [(s.document, s.page, s.chunk_id) for s in result.sources] == [
        ("SOP - Returns and Refunds.pdf", 3, "a__p3__c1"),  # higher-scoring chunk of page 3
        ("FAQ - Billing.pdf", 1, "b__p1__c0"),
        ("SOP - Returns and Refunds.pdf", 4, "a__p4__c0"),
    ]


def test_snippet_is_truncated_to_300_characters(settings: Settings, fake_retrieve: Any) -> None:
    fake_retrieve([make_chunk("a__p1__c0", 0.8, text="word   \n" * 200)])
    llm = FakeLLM(LLMAnswer(is_answerable=True, answer="x", cited_chunk_ids=["a__p1__c0"]))

    snippet = answer_question("q", settings=settings, llm=llm).sources[0].snippet

    assert snippet.endswith("...")
    assert len(snippet) <= chain_module.SNIPPET_CHARS + 3
    assert "\n" not in snippet and "  " not in snippet


def test_context_respects_token_budget_but_keeps_best_chunk(
    clean_env: Path, fake_retrieve: Any
) -> None:
    settings = Settings(_env_file=None, rag_max_context_tokens=120)
    long_text = "refund approval " * 50  # ~100 tokens
    fake_retrieve([make_chunk(f"a__p{i}__c0", 0.9 - i / 100, text=long_text) for i in range(1, 4)])
    llm = FakeLLM(LLMAnswer(is_answerable=False, answer="", cited_chunk_ids=[]))

    result = answer_question("q", settings=settings, llm=llm)
    assert len(result.contexts) == 1
    assert "a__p2__c0" not in llm.answer_calls[0][-1].content

    tiny = Settings(_env_file=None, rag_max_context_tokens=1)
    result = answer_question("q", settings=tiny, llm=llm)
    assert len(result.contexts) == 1  # the best chunk is always kept


def test_history_triggers_rewrite_and_rewritten_question_is_retrieved(
    settings: Settings, fake_retrieve: Any
) -> None:
    queries = fake_retrieve([make_chunk("t3__p7__c0", 0.8)])
    llm = FakeLLM(
        LLMAnswer(is_answerable=True, answer="3 years.", cited_chunk_ids=["t3__p7__c0"]),
        rewrite="  How long is the warranty on the Thermostat T3?\n",
    )
    history = [
        {"role": "user", "content": "Tell me about the Thermostat T3."},
        {"role": "assistant", "content": "The T3 is a smart thermostat."},
    ]

    result = answer_question("How long is its warranty?", history, settings=settings, llm=llm)

    assert len(llm.rewrite_calls) == 1
    rewrite_prompt = llm.rewrite_calls[0][-1].content
    assert "User: Tell me about the Thermostat T3." in rewrite_prompt
    assert "Assistant: The T3 is a smart thermostat." in rewrite_prompt
    assert "Latest user message: How long is its warranty?" in rewrite_prompt
    assert queries == ["How long is the warranty on the Thermostat T3?"]
    assert result.standalone_question == "How long is the warranty on the Thermostat T3?"
    assert "Question: How long is the warranty on the Thermostat T3?" in (
        llm.answer_calls[0][-1].content
    )


def test_no_history_means_no_rewrite(settings: Settings, fake_retrieve: Any) -> None:
    queries = fake_retrieve([])
    llm = FakeLLM()

    result = answer_question("  What is E4?  ", [], settings=settings, llm=llm)

    assert llm.rewrite_calls == []
    assert queries == ["What is E4?"]
    assert result.standalone_question == "What is E4?"


def test_empty_rewrite_falls_back_to_original_question(
    settings: Settings, fake_retrieve: Any
) -> None:
    queries = fake_retrieve([])
    llm = FakeLLM(rewrite="   ")

    answer_question(
        "And the T3?", [{"role": "user", "content": "T2 warranty?"}], settings=settings, llm=llm
    )

    assert queries == ["And the T3?"]


def test_history_is_truncated_to_last_turns(settings: Settings, fake_retrieve: Any) -> None:
    fake_retrieve([])
    llm = FakeLLM()
    history = [
        HistoryMessage(role="user" if i % 2 == 0 else "assistant", content=f"message-{i}")
        for i in range(10)
    ]

    answer_question("follow-up", history, settings=settings, llm=llm)

    prompt = llm.rewrite_calls[0][-1].content
    # rag_history_max_turns=2 -> last 4 messages
    assert [f"message-{i}" in prompt for i in range(10)] == [False] * 6 + [True] * 4


def test_long_history_message_is_clipped(settings: Settings, fake_retrieve: Any) -> None:
    fake_retrieve([])
    llm = FakeLLM()

    answer_question(
        "follow-up", [{"role": "assistant", "content": "x" * 10_000}], settings=settings, llm=llm
    )

    prompt = llm.rewrite_calls[0][-1].content
    assert "x" * chain_module.HISTORY_MESSAGE_MAX_CHARS + "..." in prompt
    assert "x" * (chain_module.HISTORY_MESSAGE_MAX_CHARS + 1) not in prompt


def test_history_disabled_by_zero_turns(clean_env: Path, fake_retrieve: Any) -> None:
    fake_retrieve([])
    llm = FakeLLM()
    settings = Settings(_env_file=None, rag_history_max_turns=0)

    answer_question("q", [{"role": "user", "content": "earlier"}], settings=settings, llm=llm)

    assert llm.rewrite_calls == []


def test_invalid_history_role_is_rejected(settings: Settings, fake_retrieve: Any) -> None:
    fake_retrieve([])
    with pytest.raises(ValueError):
        answer_question("q", [{"role": "system", "content": "x"}], settings=settings, llm=FakeLLM())


def test_empty_question_is_rejected(settings: Settings) -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        answer_question("   ", settings=settings, llm=ExplodingLLM())


def test_build_chat_model_uses_settings_explicitly(clean_env: Path) -> None:
    settings = Settings(
        _env_file=None,
        openai_api_key="sk-test",
        openai_base_url="https://example.invalid/v1",
        openai_chat_model="vendor/model-x",
        openai_timeout_seconds=12.5,
        openai_max_retries=4,
    )

    llm = build_chat_model(settings)

    assert llm.model_name == "vendor/model-x"
    assert llm.openai_api_base == "https://example.invalid/v1"
    assert llm.openai_api_key.get_secret_value() == "sk-test"
    assert llm.temperature == 0
    assert llm.request_timeout == 12.5
    assert llm.max_retries == 4


@pytest.mark.integration
def test_real_chain_answers_and_refuses() -> None:
    """Real API calls against the indexed sample PDFs (run `make ingest` first)."""
    answered = answer_question("How long is the warranty on the Lumora Thermostat T3?")
    assert answered.is_answerable
    assert any(
        s.document == "Product Guide - Lumora Thermostat T3.pdf" and s.page == 7
        for s in answered.sources
    )

    refused = answer_question("How do I make a pizza?")
    assert not refused.is_answerable
    assert refused.answer.startswith(REFUSAL_MESSAGE)
