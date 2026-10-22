"""RAG chain. `answer_question()` is the only public entry point.

Pipeline:

1. Rewrite a follow-up question into a standalone question when history is given
   (history is truncated to the last RAG_HISTORY_MAX_TURNS turns).
2. Retrieve the top-k chunks and drop those below RETRIEVAL_SCORE_THRESHOLD.
3. If nothing is left, refuse immediately WITHOUT calling the LLM.
4. Send the best chunks (up to RAG_MAX_CONTEXT_TOKENS), each labelled
   ``[chunk_id] (source, p.N)``, and ask for a structured `LLMAnswer`.
5. Build citations in code: only chunk IDs that were actually sent to the LLM in this
   request are kept and mapped to sources (deduplicated by document + page). An answer
   that claims to be answerable but has no valid citation is downgraded to a refusal.

Because `sources` are produced only from chunks of the current retrieval, a citation can
never point to a document or page the model invented.
"""

from __future__ import annotations

import logging
import re
import time
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_core.language_models import BaseChatModel
from langchain_openai import ChatOpenAI

from app.config import Settings, get_settings
from app.ingestion.chunker import count_tokens
from app.rag.prompts import (
    ANSWER_PROMPT,
    REFUSAL_MESSAGE,
    RELATED_DOCUMENTS_HINT,
    REWRITE_PROMPT,
)
from app.rag.schemas import (
    ChatResult,
    HistoryMessage,
    LLMAnswer,
    RefusalReason,
    Source,
)
from app.retrieval.retriever import RetrievedChunk, filter_by_threshold, retrieve

__all__ = ["answer_question"]

logger = logging.getLogger(__name__)

SNIPPET_CHARS = 300
# Upper bound for a single history message in the rewrite prompt (characters).
HISTORY_MESSAGE_MAX_CHARS = 2000
# At most this many related documents are named in a refusal.
MAX_RELATED_DOCUMENTS = 3

_WHITESPACE = re.compile(r"\s+")


@dataclass(frozen=True)
class _Generation:
    answer: str
    is_answerable: bool
    sources: list[Source]
    refusal_reason: RefusalReason | None


def build_chat_model(settings: Settings | None = None) -> ChatOpenAI:
    """Create the chat model from Settings (endpoint and key passed explicitly)."""
    s = settings or get_settings()
    return ChatOpenAI(
        model=s.openai_chat_model,
        base_url=s.openai_base_url,
        api_key=s.require_openai_api_key(),
        temperature=0,
        timeout=s.openai_timeout_seconds,
        max_retries=s.openai_max_retries,
    )


def _coerce_history(
    history: Sequence[HistoryMessage | Mapping[str, str]] | None, max_turns: int
) -> list[HistoryMessage]:
    """Validate history and keep only the last `max_turns` turns (2 messages per turn)."""
    if not history or max_turns <= 0:
        return []
    messages = [
        item if isinstance(item, HistoryMessage) else HistoryMessage.model_validate(item)
        for item in history
    ]
    messages = [m for m in messages if m.content.strip()]
    return messages[-2 * max_turns :]


def _format_history(messages: Sequence[HistoryMessage]) -> str:
    lines = []
    for message in messages:
        content = _WHITESPACE.sub(" ", message.content).strip()
        if len(content) > HISTORY_MESSAGE_MAX_CHARS:
            content = content[:HISTORY_MESSAGE_MAX_CHARS].rstrip() + "..."
        speaker = "User" if message.role == "user" else "Assistant"
        lines.append(f"{speaker}: {content}")
    return "\n".join(lines)


def _rewrite_question(question: str, history: Sequence[HistoryMessage], llm: BaseChatModel) -> str:
    """Turn a follow-up into a standalone question; returns `question` if there is no history."""
    if not history:
        return question
    messages = REWRITE_PROMPT.format_messages(history=_format_history(history), question=question)
    reply = llm.invoke(messages)
    rewritten = _WHITESPACE.sub(" ", str(reply.content)).strip()
    if not rewritten:
        logger.warning("question rewrite returned empty output; using the original question")
        return question
    return rewritten


def _select_context(chunks: Sequence[RetrievedChunk], max_tokens: int) -> list[RetrievedChunk]:
    """Take chunks best-first until the token budget is used; always keep the best one."""
    selected: list[RetrievedChunk] = []
    used = 0
    for chunk in chunks:
        tokens = count_tokens(chunk.text)
        if selected and used + tokens > max_tokens:
            break
        selected.append(chunk)
        used += tokens
    return selected


def _chunk_label(chunk: RetrievedChunk) -> str:
    return f"[{chunk.chunk_id}] ({chunk.metadata['source']}, p.{chunk.metadata['page']})"


def _format_context(chunks: Sequence[RetrievedChunk]) -> str:
    blocks = []
    for chunk in chunks:
        lines = [_chunk_label(chunk)]
        section = chunk.metadata.get("section")
        if section:
            lines.append(f"Section: {section}")
        lines.append(chunk.text.strip())
        blocks.append("\n".join(lines))
    return "\n\n---\n\n".join(blocks)


def _snippet(text: str) -> str:
    flat = _WHITESPACE.sub(" ", text).strip()
    if len(flat) <= SNIPPET_CHARS:
        return flat
    return flat[:SNIPPET_CHARS].rstrip() + "..."


def _normalize_chunk_id(raw: str) -> str:
    """Strip whitespace and label brackets the model may have copied (e.g. "[id]")."""
    return raw.strip().strip("[]").strip()


def _valid_cited_chunks(
    cited_ids: Sequence[str], context: Sequence[RetrievedChunk]
) -> list[RetrievedChunk]:
    """Return context chunks the model cited, in citation order, ignoring unknown IDs."""
    by_id = {chunk.chunk_id: chunk for chunk in context}
    valid: list[RetrievedChunk] = []
    seen: set[str] = set()
    unknown: list[str] = []
    for raw in cited_ids:
        chunk_id = _normalize_chunk_id(raw)
        chunk = by_id.get(chunk_id)
        if chunk is None:
            unknown.append(raw)
        elif chunk_id not in seen:
            seen.add(chunk_id)
            valid.append(chunk)
    if unknown:
        logger.warning(
            "dropped cited chunk ids that were not in the context",
            extra={"unknown_chunk_ids": unknown},
        )
    return valid


def _sources_from_chunks(chunks: Sequence[RetrievedChunk]) -> list[Source]:
    """Map chunks to sources, one per (document, page), keeping the highest-scoring chunk."""
    by_page: dict[tuple[str, int], RetrievedChunk] = {}
    for chunk in chunks:
        key = (str(chunk.metadata["source"]), int(chunk.metadata["page"]))
        best = by_page.get(key)
        if best is None or chunk.score > best.score:
            by_page[key] = chunk  # dict keeps first-citation order for the key
    return [
        Source(
            document=document,
            page=page,
            section=chunk.metadata.get("section"),
            snippet=_snippet(chunk.text),
            score=round(chunk.score, 4),
            chunk_id=chunk.chunk_id,
        )
        for (document, page), chunk in by_page.items()
    ]


def _refusal_text(related: Sequence[RetrievedChunk]) -> str:
    """The standard refusal, optionally naming related documents (built from metadata)."""
    if not related:
        return REFUSAL_MESSAGE
    names = [
        f"{source.document} (p. {source.page})"
        for source in _sources_from_chunks(related)[:MAX_RELATED_DOCUMENTS]
    ]
    return REFUSAL_MESSAGE + RELATED_DOCUMENTS_HINT.format(documents="; ".join(names))


def _generate(question: str, context: Sequence[RetrievedChunk], llm: BaseChatModel) -> _Generation:
    structured = llm.with_structured_output(LLMAnswer, method="function_calling")
    messages = ANSWER_PROMPT.format_messages(context=_format_context(context), question=question)
    raw = structured.invoke(messages)

    if raw is None:
        logger.warning("chat model returned no structured answer; refusing")
        return _Generation(REFUSAL_MESSAGE, False, [], RefusalReason.INVALID_MODEL_OUTPUT)
    parsed = raw if isinstance(raw, LLMAnswer) else LLMAnswer.model_validate(raw)

    cited = _valid_cited_chunks(parsed.cited_chunk_ids, context)
    if not parsed.is_answerable:
        return _Generation(_refusal_text(cited), False, [], RefusalReason.MODEL_DECLINED)
    if not cited or not parsed.answer.strip():
        logger.warning(
            "answer without valid citations downgraded to refusal",
            extra={"cited_chunk_ids": parsed.cited_chunk_ids},
        )
        return _Generation(REFUSAL_MESSAGE, False, [], RefusalReason.NO_VALID_CITATIONS)
    return _Generation(parsed.answer.strip(), True, _sources_from_chunks(cited), None)


def answer_question(
    question: str,
    history: Sequence[HistoryMessage | Mapping[str, str]] | None = None,
    *,
    settings: Settings | None = None,
    llm: BaseChatModel | None = None,
    vectorstore: Chroma | None = None,
) -> ChatResult:
    """Answer `question` from the indexed documents, with code-built citations.

    `history` holds previous messages (`{"role": "user"|"assistant", "content": ...}`),
    oldest first; only the last RAG_HISTORY_MAX_TURNS turns are used. `llm` and
    `vectorstore` can be injected (API lifespan, tests); by default they are built from
    Settings. OpenAI errors (after the configured retries) propagate to the caller.
    """
    started = time.perf_counter()
    s = settings or get_settings()
    question = question.strip()
    if not question:
        raise ValueError("question must not be empty")

    turns = _coerce_history(history, s.rag_history_max_turns)
    chat_model = llm

    def get_llm() -> BaseChatModel:
        nonlocal chat_model
        if chat_model is None:
            chat_model = build_chat_model(s)
        return chat_model

    standalone = _rewrite_question(question, turns, get_llm()) if turns else question

    retrieved = retrieve(standalone, k=s.retrieval_top_k, vectorstore=vectorstore, settings=s)
    relevant = filter_by_threshold(retrieved, s.retrieval_score_threshold)
    context = _select_context(relevant, s.rag_max_context_tokens)

    if not context:
        generation = _Generation(REFUSAL_MESSAGE, False, [], RefusalReason.NO_RELEVANT_CHUNKS)
    else:
        generation = _generate(standalone, context, get_llm())

    latency_ms = int((time.perf_counter() - started) * 1000)
    logger.info(
        "answered question",
        extra={
            "is_answerable": generation.is_answerable,
            "refusal_reason": generation.refusal_reason,
            "rewritten": standalone != question,
            "history_messages": len(turns),
            "retrieved": len(retrieved),
            "above_threshold": len(relevant),
            "context_chunks": len(context),
            "sources": len(generation.sources),
            "top_score": round(retrieved[0].score, 4) if retrieved else None,
            "latency_ms": latency_ms,
        },
    )
    return ChatResult(
        answer=generation.answer,
        is_answerable=generation.is_answerable,
        sources=generation.sources,
        model=s.openai_chat_model,
        latency_ms=latency_ms,
        standalone_question=standalone,
        refusal_reason=generation.refusal_reason,
        contexts=[chunk.text for chunk in context],
    )
