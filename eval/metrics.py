"""Per-question evaluation records, custom metrics and failure diagnosis.

Everything here is pure computation (no API calls), so it is covered by unit tests.

Custom metrics (see `aggregate()`):

- citation hit rate: share of in-scope questions whose cited sources include at least one
  expected (document, page). A refused in-scope question counts as a miss.
- out-of-scope refusal rate: share of out-of-scope questions that were refused.
- in-scope false refusal rate: share of in-scope questions that were refused.
- key fact accuracy: share of in-scope questions whose answer contains every key fact
  listed for the question (a deterministic correctness check; refusals count as misses).
- retrieval hit rate: share of in-scope questions whose expected page is among the top-k
  retrieved chunks (before the score threshold); a diagnostic for the retriever alone.
- average latency and average cost per question (chat tokens + query embedding tokens).
"""

from __future__ import annotations

import math
import re
import statistics
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from enum import StrEnum

from pydantic import BaseModel, Field

from eval.dataset import Category, EvalQuestion

RAGAS_METRICS: tuple[str, ...] = (
    "faithfulness",
    "answer_relevancy",
    "context_precision",
    "context_recall",
)

# Answers below this faithfulness are reported as failures even when the citation is right.
LOW_FAITHFULNESS = 0.7


@dataclass(frozen=True)
class Targets:
    """Quality targets the summary reports against."""

    faithfulness: float = 0.85
    citation_hit_rate: float = 0.85
    out_of_scope_refusal_rate: float = 1.0
    false_refusal_rate: float = 0.10


@dataclass(frozen=True)
class Pricing:
    """USD prices per 1M tokens used for the cost estimate.

    Defaults are the OpenAI list prices of gpt-4o-mini (chat) and text-embedding-3-small
    (embeddings). Override them with the CLI flags when another model is configured.
    """

    chat_input_per_m: float = 0.15
    chat_output_per_m: float = 0.60
    embedding_per_m: float = 0.02

    def cost(self, input_tokens: int, output_tokens: int, embedding_tokens: int) -> float:
        return (
            input_tokens * self.chat_input_per_m
            + output_tokens * self.chat_output_per_m
            + embedding_tokens * self.embedding_per_m
        ) / 1_000_000


class RetrievedPage(BaseModel):
    """One retrieved chunk, reduced to what the report needs."""

    document: str
    page: int
    score: float
    in_context: bool = Field(description="True if the chunk was sent to the LLM.")

    @property
    def label(self) -> str:
        return f"{self.document} p.{self.page}"


class Diagnosis(StrEnum):
    """Outcome of one question; everything except OK is reported as a failure."""

    OK = "ok"
    ERROR = "error"
    # In-scope questions that were refused.
    RETRIEVAL_MISS = "retrieval_miss"  # expected page not in the top-k
    BELOW_THRESHOLD = "below_threshold"  # retrieved, but scored under the threshold
    CONTEXT_BUDGET = "context_budget"  # above threshold, cut by the context token budget
    MODEL_DECLINED = "model_declined"  # in the context, but the model said "not answerable"
    # In-scope questions that were answered.
    WRONG_SOURCE = "wrong_source"  # answered from other pages; expected page not in context
    CITATION_MISS = "citation_miss"  # expected page was in context but not cited
    MISSING_KEY_FACTS = "missing_key_facts"  # cited correctly, but key facts are missing
    LOW_FAITHFULNESS = "low_faithfulness"  # cited correctly, but claims not supported
    # Out-of-scope questions.
    ANSWERED_OUT_OF_SCOPE = "answered_out_of_scope"


class QuestionResult(BaseModel):
    """Everything recorded for one evaluation question."""

    id: str
    category: Category
    question: str
    should_answer: bool
    ground_truth: str
    expected_sources: list[str]
    expected_pages: list[tuple[str, int]]
    key_facts: list[str] = Field(default_factory=list)

    answer: str = ""
    answered: bool = False
    refusal_reason: str | None = None
    standalone_question: str = ""
    cited_sources: list[tuple[str, int]] = Field(default_factory=list)
    contexts: list[str] = Field(default_factory=list)
    retrieved: list[RetrievedPage] = Field(default_factory=list)

    latency_ms: int = 0
    input_tokens: int = 0
    output_tokens: int = 0
    embedding_tokens: int = 0
    cost_usd: float = 0.0

    scores: dict[str, float | None] = Field(default_factory=dict)
    score_errors: dict[str, str] = Field(default_factory=dict)
    error: str | None = None

    diagnosis: Diagnosis = Diagnosis.OK
    diagnosis_detail: str = ""

    @classmethod
    def for_question(cls, question: EvalQuestion) -> QuestionResult:
        return cls(
            id=question.id,
            category=question.category,
            question=question.question,
            should_answer=question.should_answer,
            ground_truth=question.ground_truth,
            expected_sources=[
                f"{s.document} p.{','.join(str(p) for p in s.pages)}"
                for s in question.expected_sources
            ],
            expected_pages=sorted(question.expected_pages()),
            key_facts=list(question.key_facts),
        )

    @property
    def refused(self) -> bool:
        return self.error is None and not self.answered

    @property
    def citation_hit(self) -> bool | None:
        """True if a cited (document, page) is expected; None for out-of-scope questions."""
        if not self.should_answer:
            return None
        return bool(set(self.cited_sources) & set(self.expected_pages))

    @property
    def missing_key_facts(self) -> list[str]:
        """Key facts not found in the answer (all of them when the question was refused)."""
        if not self.answered:
            return list(self.key_facts)
        return [fact for fact in self.key_facts if not contains_fact(self.answer, fact)]

    @property
    def key_facts_ok(self) -> bool | None:
        """True if the answer has every key fact; None when no key facts are defined."""
        if not self.should_answer or not self.key_facts:
            return None
        return not self.missing_key_facts

    @property
    def expected_rank(self) -> int | None:
        """1-based rank of the first retrieved chunk from an expected page (None if absent)."""
        expected = set(self.expected_pages)
        for rank, chunk in enumerate(self.retrieved, start=1):
            if (chunk.document, chunk.page) in expected:
                return rank
        return None

    @property
    def top_score(self) -> float | None:
        return self.retrieved[0].score if self.retrieved else None

    @property
    def passed(self) -> bool:
        return self.diagnosis is Diagnosis.OK


_SPACES = re.compile(r"\s+")


def _normalize(text: str) -> str:
    """Lowercase, drop thousands separators, unify dashes and collapse whitespace."""
    text = text.lower().replace(",", "").replace("\u2011", "-").replace("\u2013", "-")
    return _SPACES.sub(" ", text).strip()


def contains_fact(answer: str, fact: str) -> bool:
    """True if `answer` contains `fact` or one of its "|"-separated alternatives."""
    haystack = _normalize(answer)
    return any(_normalize(alt) in haystack for alt in fact.split("|") if alt.strip())


def _expected_chunks(result: QuestionResult) -> list[RetrievedPage]:
    expected = set(result.expected_pages)
    return [c for c in result.retrieved if (c.document, c.page) in expected]


def _cited_labels(result: QuestionResult) -> str:
    return ", ".join(f"{doc} p.{page}" for doc, page in result.cited_sources) or "nothing"


def diagnose(result: QuestionResult, threshold: float) -> tuple[Diagnosis, str]:
    """Classify the outcome of one question and explain it in plain English."""
    if result.error is not None:
        return Diagnosis.ERROR, f"The pipeline raised an error: {result.error}"

    top = f"{result.top_score:.2f}" if result.top_score is not None else "n/a"
    if not result.should_answer:
        if result.refused:
            return Diagnosis.OK, "Correctly refused."
        return (
            Diagnosis.ANSWERED_OUT_OF_SCOPE,
            "The documents do not contain this answer, but the assistant answered it "
            f"(cited {_cited_labels(result)}). The best retrieval score was {top} against a "
            f"threshold of {threshold:.2f}, so the question reached the model, which then "
            "did not decline.",
        )

    expected = _expected_chunks(result)
    in_context = [c for c in expected if c.in_context]
    if result.refused:
        if not expected:
            return (
                Diagnosis.RETRIEVAL_MISS,
                "The page with the answer was not among the top retrieved passages, so the "
                "assistant (correctly, given what it saw) said it could not find the answer. "
                f"Best retrieved: {result.retrieved[0].label if result.retrieved else 'none'} "
                f"(score {top}).",
            )
        best = expected[0]
        if best.score < threshold:
            return (
                Diagnosis.BELOW_THRESHOLD,
                f"The right page ({best.label}) was retrieved with score {best.score:.2f}, "
                f"below the relevance threshold of {threshold:.2f}, so it was filtered out "
                "before the model saw it.",
            )
        if not in_context:
            return (
                Diagnosis.CONTEXT_BUDGET,
                f"The right page ({best.label}) passed the threshold but did not fit into "
                "the context token budget sent to the model.",
            )
        return (
            Diagnosis.MODEL_DECLINED,
            f"The right page ({in_context[0].label}) was given to the model, but the model "
            "judged that it did not answer the question and declined.",
        )

    if not result.citation_hit:
        if not in_context:
            return (
                Diagnosis.WRONG_SOURCE,
                f"The expected page was not in the context; the answer was based on "
                f"{_cited_labels(result)} instead.",
            )
        return (
            Diagnosis.CITATION_MISS,
            f"The expected page ({in_context[0].label}) was in the context, but the answer "
            f"cited {_cited_labels(result)} instead.",
        )

    missing = result.missing_key_facts
    if missing:
        return (
            Diagnosis.MISSING_KEY_FACTS,
            "The right page was cited, but the answer is incomplete or wrong: it does not "
            f"contain {', '.join(repr(m.split('|')[0]) for m in missing)}.",
        )

    faithfulness = result.scores.get("faithfulness")
    if faithfulness is not None and faithfulness < LOW_FAITHFULNESS:
        return (
            Diagnosis.LOW_FAITHFULNESS,
            f"The right page was cited, but only {faithfulness:.0%} of the statements in the "
            "answer are supported by the retrieved passages (RAGAS faithfulness).",
        )
    return Diagnosis.OK, "Answered with a correct citation."


def _ratio(numerator: int, denominator: int) -> float | None:
    return numerator / denominator if denominator else None


def _mean(values: Iterable[float | None]) -> float | None:
    clean = [v for v in values if v is not None and not math.isnan(v)]
    return statistics.fmean(clean) if clean else None


def aggregate(results: Sequence[QuestionResult]) -> dict[str, float | int | None]:
    """Compute the headline metrics for a run."""
    in_scope = [r for r in results if r.should_answer]
    out_of_scope = [r for r in results if not r.should_answer]
    with_facts = [r for r in in_scope if r.key_facts]
    latencies = [r.latency_ms for r in results if r.error is None]

    metrics: dict[str, float | int | None] = {
        "questions": len(results),
        "in_scope_questions": len(in_scope),
        "out_of_scope_questions": len(out_of_scope),
        "errors": sum(r.error is not None for r in results),
        "passed": sum(r.passed for r in results),
        "citation_hit_rate": _ratio(sum(bool(r.citation_hit) for r in in_scope), len(in_scope)),
        "out_of_scope_refusal_rate": _ratio(
            sum(r.refused for r in out_of_scope), len(out_of_scope)
        ),
        "false_refusal_rate": _ratio(sum(r.refused for r in in_scope), len(in_scope)),
        "key_fact_accuracy": _ratio(sum(bool(r.key_facts_ok) for r in with_facts), len(with_facts)),
        "retrieval_hit_rate": _ratio(
            sum(r.expected_rank is not None for r in in_scope), len(in_scope)
        ),
        "avg_latency_ms": statistics.fmean(latencies) if latencies else None,
        "p95_latency_ms": _percentile(latencies, 0.95),
        "avg_cost_usd": _mean(r.cost_usd for r in results if r.error is None),
        "total_cost_usd": sum(r.cost_usd for r in results),
    }
    for name in RAGAS_METRICS:
        metrics[name] = _mean(r.scores.get(name) for r in in_scope)
        metrics[f"{name}_count"] = sum(r.scores.get(name) is not None for r in in_scope)
    return metrics


def _percentile(values: Sequence[int], fraction: float) -> float | None:
    """Nearest-rank percentile (no interpolation); None for an empty list."""
    if not values:
        return None
    ordered = sorted(values)
    index = max(0, math.ceil(fraction * len(ordered)) - 1)
    return float(ordered[index])


def target_checks(
    metrics: dict[str, float | int | None], targets: Targets
) -> list[tuple[str, float | None, str, bool | None]]:
    """(metric name, value, target text, met?) for every metric with a target."""

    def check(value: float | int | None, ok: bool) -> bool | None:
        return None if value is None else ok

    faith = metrics.get("faithfulness")
    hit = metrics.get("citation_hit_rate")
    oos = metrics.get("out_of_scope_refusal_rate")
    false_refusal = metrics.get("false_refusal_rate")
    return [
        (
            "faithfulness",
            faith,
            f">= {targets.faithfulness:.2f}",
            check(faith, faith is not None and faith >= targets.faithfulness),
        ),
        (
            "citation_hit_rate",
            hit,
            f">= {targets.citation_hit_rate:.0%}",
            check(hit, hit is not None and hit >= targets.citation_hit_rate),
        ),
        (
            "out_of_scope_refusal_rate",
            oos,
            f"= {targets.out_of_scope_refusal_rate:.0%}",
            check(oos, oos is not None and oos >= targets.out_of_scope_refusal_rate),
        ),
        (
            "false_refusal_rate",
            false_refusal,
            f"<= {targets.false_refusal_rate:.0%}",
            check(
                false_refusal,
                false_refusal is not None and false_refusal <= targets.false_refusal_rate,
            ),
        ),
    ]
