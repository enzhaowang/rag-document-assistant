"""RAGAS scoring of in-scope evaluation questions (real LLM and embedding calls).

Uses the RAGAS v0.4 metric collections with the endpoint, key and models from Settings
(any OpenAI-compatible endpoint works). Scored only for questions with
should_answer=true:

- faithfulness, answer_relevancy: only when the question was answered; a refusal makes no
  claims, so these are left empty for refused questions;
- context_precision, context_recall: always; when no passage passed the retrieval
  threshold the context is empty and both are 0.

A metric that fails for one question (timeout, malformed judge output) is recorded as
empty with the error message; it never aborts the run.
"""

from __future__ import annotations

import asyncio
import logging
import os
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from app.config import Settings
from eval.metrics import QuestionResult

logger = logging.getLogger(__name__)

# Opt out of RAGAS usage analytics before ragas is imported.
os.environ.setdefault("RAGAS_DO_NOT_TRACK", "true")

# Judge calls can be slower than chat calls (long prompts with all passages).
JUDGE_TIMEOUT_FACTOR = 3


@dataclass
class RagasScorers:
    """The four RAGAS metric objects sharing one judge LLM."""

    faithfulness: Any
    answer_relevancy: Any
    context_precision: Any
    context_recall: Any


def build_scorers(settings: Settings, judge_model: str | None = None) -> RagasScorers:
    """Create the RAGAS metrics with the configured endpoint (no SDK env lookups)."""
    from openai import AsyncOpenAI
    from ragas.embeddings import OpenAIEmbeddings as RagasOpenAIEmbeddings
    from ragas.llms import llm_factory
    from ragas.metrics.collections import (
        AnswerRelevancy,
        ContextPrecision,
        ContextRecall,
        Faithfulness,
    )

    timeout = settings.openai_timeout_seconds * JUDGE_TIMEOUT_FACTOR
    chat_client = AsyncOpenAI(
        base_url=settings.openai_base_url,
        api_key=settings.require_openai_api_key(),
        timeout=timeout,
        max_retries=settings.openai_max_retries,
    )
    embedding_client = AsyncOpenAI(
        base_url=settings.embedding_base_url,
        api_key=settings.require_embedding_api_key(),
        timeout=timeout,
        max_retries=settings.openai_max_retries,
    )
    llm = llm_factory(
        judge_model or settings.openai_chat_model,
        client=chat_client,
        temperature=0,
        max_tokens=4096,
    )
    embeddings = RagasOpenAIEmbeddings(
        client=embedding_client, model=settings.openai_embedding_model
    )
    return RagasScorers(
        faithfulness=Faithfulness(llm=llm),
        answer_relevancy=AnswerRelevancy(llm=llm, embeddings=embeddings),
        context_precision=ContextPrecision(llm=llm),
        context_recall=ContextRecall(llm=llm),
    )


async def _score_one(
    name: str, metric: Any, kwargs: dict[str, Any], semaphore: asyncio.Semaphore
) -> tuple[float | None, str | None]:
    async with semaphore:
        try:
            outcome = await metric.ascore(**kwargs)
        except Exception as exc:  # noqa: BLE001 - one failed metric must not stop the run
            logger.warning("ragas metric failed", extra={"metric": name, "error": str(exc)})
            return None, f"{type(exc).__name__}: {exc}"
    value = getattr(outcome, "value", outcome)
    try:
        return float(value), None
    except (TypeError, ValueError):
        return None, f"non-numeric score: {value!r}"


async def _score_result(
    scorers: RagasScorers, result: QuestionResult, semaphore: asyncio.Semaphore
) -> None:
    jobs: dict[str, tuple[Any, dict[str, Any]]] = {}
    question = result.question
    if result.answered:
        jobs["faithfulness"] = (
            scorers.faithfulness,
            {
                "user_input": question,
                "response": result.answer,
                "retrieved_contexts": result.contexts,
            },
        )
        jobs["answer_relevancy"] = (
            scorers.answer_relevancy,
            {"user_input": question, "response": result.answer},
        )
    else:
        result.score_errors["faithfulness"] = "not scored: question was refused"
        result.score_errors["answer_relevancy"] = "not scored: question was refused"

    if result.contexts:
        context_kwargs = {
            "user_input": question,
            "reference": result.ground_truth,
            "retrieved_contexts": result.contexts,
        }
        jobs["context_precision"] = (scorers.context_precision, context_kwargs)
        jobs["context_recall"] = (scorers.context_recall, context_kwargs)
    else:
        result.scores["context_precision"] = 0.0
        result.scores["context_recall"] = 0.0

    names = list(jobs)
    outcomes = await asyncio.gather(*(_score_one(name, *jobs[name], semaphore) for name in names))
    for name, (value, error) in zip(names, outcomes, strict=True):
        result.scores[name] = value
        if error:
            result.score_errors[name] = error


async def _score_all(
    scorers: RagasScorers, results: Sequence[QuestionResult], concurrency: int
) -> None:
    semaphore = asyncio.Semaphore(concurrency)
    await asyncio.gather(*(_score_result(scorers, r, semaphore) for r in results))


def score_results(
    results: Sequence[QuestionResult],
    settings: Settings,
    *,
    judge_model: str | None = None,
    concurrency: int = 4,
    scorers: RagasScorers | None = None,
) -> None:
    """Fill `result.scores` with RAGAS metrics for every in-scope, error-free result."""
    targets = [r for r in results if r.should_answer and r.error is None]
    if not targets:
        return
    active = scorers or build_scorers(settings, judge_model)
    asyncio.run(_score_all(active, targets, max(1, concurrency)))
