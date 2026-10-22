"""Run evaluation questions through `answer_question()` and record what happened.

Shared by `eval/run_eval.py` (full evaluation with RAGAS) and `eval/tune.py` (parameter
sweeps with the custom metrics only). Real API calls; nothing here is mocked.
"""

from __future__ import annotations

import logging
from collections.abc import Sequence
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from langchain_chroma import Chroma
from langchain_core.callbacks import get_usage_metadata_callback
from langchain_core.language_models import BaseChatModel

from app.config import Settings
from app.ingestion.chunker import count_tokens
from app.ingestion.pipeline import ingest, load_and_chunk
from app.rag.chain import answer_question, build_chat_model
from app.retrieval.retriever import retrieve
from app.retrieval.vectorstore import get_vectorstore
from eval.dataset import EvalQuestion
from eval.metrics import Pricing, QuestionResult, RetrievedPage, diagnose

logger = logging.getLogger(__name__)


class IndexNotReadyError(RuntimeError):
    """The configured collection is empty or does not match the PDFs and chunk settings."""


@dataclass(frozen=True)
class EvalConfig:
    """Retrieval and chunking parameters of one evaluation run."""

    top_k: int
    threshold: float
    chunk_size: int
    chunk_overlap: int

    @classmethod
    def from_settings(cls, settings: Settings) -> EvalConfig:
        return cls(
            top_k=settings.retrieval_top_k,
            threshold=settings.retrieval_score_threshold,
            chunk_size=settings.chunk_size_tokens,
            chunk_overlap=settings.chunk_overlap_tokens,
        )

    @property
    def label(self) -> str:
        return (
            f"chunk {self.chunk_size}/{self.chunk_overlap}, top-k {self.top_k}, "
            f"threshold {self.threshold:.2f}"
        )


def settings_for(base: Settings, config: EvalConfig) -> Settings:
    """Copy `base` with the run's parameters.

    When the chunking differs from the configured one, the run uses a separate collection
    (``<CHROMA_COLLECTION>_eval_cs<size>_ov<overlap>``) so the main index is never touched.
    """
    update: dict[str, object] = {
        "retrieval_top_k": config.top_k,
        "retrieval_score_threshold": config.threshold,
        "chunk_size_tokens": config.chunk_size,
        "chunk_overlap_tokens": config.chunk_overlap,
    }
    if (config.chunk_size, config.chunk_overlap) != (
        base.chunk_size_tokens,
        base.chunk_overlap_tokens,
    ):
        update["chroma_collection"] = (
            f"{base.chroma_collection}_eval_cs{config.chunk_size}_ov{config.chunk_overlap}"
        )
    if config.chunk_overlap >= config.chunk_size:
        raise ValueError("chunk overlap must be smaller than chunk size")
    return base.model_copy(update=update)


def prepare_vectorstore(settings: Settings, base: Settings) -> Chroma:
    """Return the store for `settings`, checking (main index) or building (eval index) it.

    The configured collection is only checked: it must contain exactly the chunks that the
    current PDFs and chunk settings produce, otherwise `IndexNotReadyError` asks for
    `make ingest`. A separate eval collection is synced with `ingest()` (cheap when it is
    already up to date).
    """
    store = get_vectorstore(settings)
    if settings.chroma_collection != base.chroma_collection:
        logger.info("syncing eval collection", extra={"collection": settings.chroma_collection})
        ingest(settings.pdf_dir, settings, vectorstore=store)
        return store

    expected = {chunk.metadata["chunk_id"] for chunk in load_and_chunk(settings.pdf_dir, settings)}
    stored = set(store.get(include=[])["ids"])
    if not stored:
        raise IndexNotReadyError(
            f"Collection {settings.chroma_collection!r} is empty. Run `make ingest` first."
        )
    if stored != expected:
        raise IndexNotReadyError(
            f"Collection {settings.chroma_collection!r} does not match the PDFs in "
            f"{settings.pdf_dir} with CHUNK_SIZE_TOKENS={settings.chunk_size_tokens} and "
            f"CHUNK_OVERLAP_TOKENS={settings.chunk_overlap_tokens} "
            f"({len(stored)} stored vs {len(expected)} expected chunks). Run `make ingest`."
        )
    return store


def run_question(
    question: EvalQuestion,
    settings: Settings,
    store: Chroma,
    llm: BaseChatModel,
    pricing: Pricing,
) -> QuestionResult:
    """Answer one question and record the answer, citations, retrieval, tokens and cost."""
    result = QuestionResult.for_question(question)
    try:
        with get_usage_metadata_callback() as usage:
            chat = answer_question(question.question, settings=settings, llm=llm, vectorstore=store)
        # Diagnostics only: the same query again, to see every top-k page with its score
        # (deterministic, so it matches what the chain retrieved).
        retrieved = retrieve(
            chat.standalone_question,
            k=settings.retrieval_top_k,
            vectorstore=store,
            settings=settings,
        )
    except Exception as exc:  # noqa: BLE001 - record the failure and keep evaluating
        logger.exception("question failed", extra={"question_id": question.id})
        result.error = f"{type(exc).__name__}: {exc}"
        return result

    result.answer = chat.answer
    result.answered = chat.is_answerable
    result.refusal_reason = str(chat.refusal_reason) if chat.refusal_reason else None
    result.standalone_question = chat.standalone_question
    result.cited_sources = [(source.document, source.page) for source in chat.sources]
    result.contexts = list(chat.contexts)
    result.latency_ms = chat.latency_ms

    context_texts = set(chat.contexts)
    result.retrieved = [
        RetrievedPage(
            document=str(chunk.metadata["source"]),
            page=int(chunk.metadata["page"]),
            score=round(chunk.score, 4),
            in_context=chunk.text in context_texts,
        )
        for chunk in retrieved
    ]

    for counts in usage.usage_metadata.values():
        result.input_tokens += int(counts.get("input_tokens", 0))
        result.output_tokens += int(counts.get("output_tokens", 0))
    result.embedding_tokens = count_tokens(chat.standalone_question)
    result.cost_usd = pricing.cost(
        result.input_tokens, result.output_tokens, result.embedding_tokens
    )
    return result


def run_questions(
    questions: Sequence[EvalQuestion],
    settings: Settings,
    store: Chroma,
    *,
    pricing: Pricing,
    llm: BaseChatModel | None = None,
    workers: int = 1,
) -> list[QuestionResult]:
    """Run all questions (in order of `questions`) and diagnose each result.

    `workers=1` runs sequentially, which keeps latency numbers free of contention; tuning
    sweeps use more workers.
    """
    model = llm or build_chat_model(settings)

    def one(question: EvalQuestion) -> QuestionResult:
        return run_question(question, settings, store, model, pricing)

    if workers <= 1:
        results = [one(q) for q in questions]
    else:
        with ThreadPoolExecutor(max_workers=workers) as pool:
            results = list(pool.map(one, questions))
    rediagnose(results, settings.retrieval_score_threshold)
    return results


def rediagnose(results: Sequence[QuestionResult], threshold: float) -> None:
    """(Re)compute the diagnosis of every result, e.g. after RAGAS scores were added."""
    for result in results:
        result.diagnosis, result.diagnosis_detail = diagnose(result, threshold)
