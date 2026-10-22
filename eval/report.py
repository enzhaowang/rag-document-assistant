"""Write evaluation reports: results.csv, metrics.json and a client-facing summary.md.

summary.md is written for a non-technical reader: conclusions first, then the scorecard,
then the details (tuning, failure analysis, per-question table, method).
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd

from eval.dataset import CATEGORY_LABELS, Category
from eval.metrics import (
    RAGAS_METRICS,
    Diagnosis,
    Pricing,
    QuestionResult,
    Targets,
    target_checks,
)

METRIC_LABELS: dict[str, str] = {
    "faithfulness": "Faithfulness",
    "answer_relevancy": "Answer relevancy",
    "context_precision": "Context precision",
    "context_recall": "Context recall",
    "citation_hit_rate": "Citation hit rate",
    "key_fact_accuracy": "Key fact accuracy",
    "out_of_scope_refusal_rate": "Out-of-scope refusal rate",
    "false_refusal_rate": "In-scope false refusal rate",
    "retrieval_hit_rate": "Retrieval hit rate (top-k)",
    "avg_latency_ms": "Average latency",
    "p95_latency_ms": "95th percentile latency",
    "avg_cost_usd": "Average cost per question",
}

METRIC_MEANINGS: dict[str, str] = {
    "faithfulness": "Share of statements in an answer that are backed by the source passages "
    "(no made-up facts).",
    "answer_relevancy": "How directly the answer addresses the question.",
    "context_precision": "Whether the passages that contain the answer are ranked first.",
    "context_recall": "Whether the passages given to the model contain everything in the "
    "reference answer.",
    "citation_hit_rate": "Answers that cite the correct document and page.",
    "key_fact_accuracy": "Answers that contain every key fact of the reference answer "
    "(numbers, names, codes), checked word for word.",
    "out_of_scope_refusal_rate": "Questions the documents do not cover that the assistant "
    "declined instead of guessing.",
    "false_refusal_rate": "Questions the documents do cover that the assistant wrongly declined.",
    "retrieval_hit_rate": "Questions where the page with the answer was among the passages "
    "retrieved by the search step.",
}

ANSWERED_FAILURE_LABELS: dict[Diagnosis, str] = {
    Diagnosis.WRONG_SOURCE: "Answered from a wrong page",
    Diagnosis.CITATION_MISS: "Wrong citation",
    Diagnosis.MISSING_KEY_FACTS: "Incomplete answer",
    Diagnosis.LOW_FAITHFULNESS: "Answered, low faithfulness",
}

RATE_METRICS = {
    "citation_hit_rate",
    "key_fact_accuracy",
    "out_of_scope_refusal_rate",
    "false_refusal_rate",
    "retrieval_hit_rate",
}

RECOMMENDATIONS: dict[Diagnosis, str] = {
    Diagnosis.RETRIEVAL_MISS: "Some answers were never retrieved. Raise RETRIEVAL_TOP_K, "
    "add hybrid keyword search (BM25) for exact terms such as codes and amounts, or add "
    "the document and section title to each chunk before embedding.",
    Diagnosis.BELOW_THRESHOLD: "Correct passages were filtered out by the relevance "
    "threshold. Lower RETRIEVAL_SCORE_THRESHOLD slightly; out-of-scope questions are still "
    "caught by the model-level refusal.",
    Diagnosis.CONTEXT_BUDGET: "Relevant passages did not fit into the context sent to the "
    "model. Raise RAG_MAX_CONTEXT_TOKENS or lower RETRIEVAL_TOP_K so the best passages fit.",
    Diagnosis.MODEL_DECLINED: "The model declined although the answer was in the passages. "
    "Review the wording of those passages (tables, abbreviations) and the answer prompt, or "
    "try a stronger chat model.",
    Diagnosis.WRONG_SOURCE: "Some answers came from a similar but wrong page. Add metadata "
    "filters (for example by product model) or a reranking step.",
    Diagnosis.CITATION_MISS: "The model answered from the right passage but cited another. "
    "Tighten the citation instruction in the prompt.",
    Diagnosis.MISSING_KEY_FACTS: "Some answers cite the right page but leave out or mix up "
    "details, typically in tables that continue on the next page. Use table-aware parsing "
    "(keep each table, with its header, in one chunk even across a page break) and ask the "
    "model to reproduce every row when listing table contents.",
    Diagnosis.LOW_FAITHFULNESS: "Some answers contain statements that are not in the "
    "passages. Tighten the prompt ('only facts from the excerpts') or use a stronger model.",
    Diagnosis.ANSWERED_OUT_OF_SCOPE: "The assistant answered a question the documents do not "
    "cover. Raise RETRIEVAL_SCORE_THRESHOLD or strengthen the refusal rules in the prompt.",
    Diagnosis.ERROR: "Some questions failed with an error; check API limits and timeouts.",
}

GENERAL_RECOMMENDATIONS = (
    "Re-run this evaluation with 15-20 real questions from your support team before go-live; "
    "the harness is ready (`eval/questions.yaml` + `make eval`).",
    "Keep the evaluation in the delivery checklist: re-run `make eval` after adding documents "
    "or changing models, and compare against this report.",
    "Most questions that are not covered by the documents still look similar to real topics "
    "(for example a product feature that is not documented). They are caught by the model's "
    "refusal, not by the score threshold, so keep out-of-scope questions in every test set.",
)


@dataclass
class RunInfo:
    """Context of an evaluation run, shown in the report and saved in metrics.json."""

    generated_at: str
    config: dict[str, Any]
    chat_model: str
    embedding_model: str
    judge_model: str | None
    pricing: Pricing
    targets: Targets = field(default_factory=Targets)
    ragas: bool = True
    label: str | None = None


# --------------------------------------------------------------------------- formatting


def fmt_metric(name: str, value: float | int | None) -> str:
    if value is None:
        return "n/a"
    if name in RATE_METRICS:
        return f"{value:.0%}"
    if name.endswith("_ms"):
        return f"{value / 1000:.1f} s"
    if name.endswith("_usd"):
        return f"${value:.5f}"
    return f"{value:.2f}"


def _cell(text: object) -> str:
    """Make text safe for a Markdown table cell."""
    return str(text).replace("|", "\\|").replace("\n", " ").strip()


def _short(text: str, limit: int = 160) -> str:
    flat = " ".join(text.split())
    return flat if len(flat) <= limit else flat[: limit - 3].rstrip() + "..."


def _status(met: bool | None) -> str:
    return {True: "Met", False: "Not met", None: "n/a"}[met]


def _pages(pairs: Sequence[tuple[str, int]]) -> str:
    return "; ".join(f"{doc} p.{page}" for doc, page in pairs) or "-"


def _score(result: QuestionResult, name: str) -> str:
    value = result.scores.get(name)
    return "-" if value is None else f"{value:.2f}"


def _outcome(result: QuestionResult) -> str:
    if result.error:
        return "Error"
    if not result.should_answer:
        return "Refused (correct)" if result.refused else "Answered (wrong)"
    if result.refused:
        return "Refused (wrong)"
    if result.passed:
        return "Answered"
    return ANSWERED_FAILURE_LABELS.get(result.diagnosis, result.diagnosis.value)


# --------------------------------------------------------------------------- csv / json


def results_frame(results: Sequence[QuestionResult]) -> pd.DataFrame:
    rows = []
    for r in results:
        row: dict[str, Any] = {
            "id": r.id,
            "category": r.category.value,
            "question": r.question,
            "should_answer": r.should_answer,
            "answered": r.answered,
            "refusal_reason": r.refusal_reason,
            "citation_hit": r.citation_hit,
            "key_facts_ok": r.key_facts_ok,
            "missing_key_facts": "; ".join(r.missing_key_facts) if r.should_answer else None,
            "passed": r.passed,
            "diagnosis": r.diagnosis.value,
            "diagnosis_detail": r.diagnosis_detail,
            "expected_sources": "; ".join(r.expected_sources),
            "cited_sources": _pages(r.cited_sources),
            "expected_rank": r.expected_rank,
            "top_score": r.top_score,
            "retrieved": "; ".join(
                f"{c.label} ({c.score:.3f}{'' if c.in_context else ', not sent'})"
                for c in r.retrieved
            ),
        }
        for name in RAGAS_METRICS:
            row[name] = r.scores.get(name)
        row.update(
            {
                "latency_ms": r.latency_ms,
                "input_tokens": r.input_tokens,
                "output_tokens": r.output_tokens,
                "embedding_tokens": r.embedding_tokens,
                "cost_usd": round(r.cost_usd, 7),
                "answer": r.answer,
                "ground_truth": r.ground_truth,
                "standalone_question": r.standalone_question,
                "error": r.error,
                "score_errors": json.dumps(r.score_errors) if r.score_errors else None,
            }
        )
        rows.append(row)
    return pd.DataFrame(rows)


def metrics_document(metrics: Mapping[str, Any], info: RunInfo) -> dict[str, Any]:
    return {
        "generated_at": info.generated_at,
        "config": info.config,
        "models": {
            "chat": info.chat_model,
            "embedding": info.embedding_model,
            "judge": info.judge_model,
        },
        "pricing_usd_per_1m_tokens": asdict(info.pricing),
        "ragas": info.ragas,
        "label": info.label,
        "targets": asdict(info.targets),
        "metrics": dict(metrics),
    }


# --------------------------------------------------------------------------- summary.md


def _mix_text(results: Sequence[QuestionResult]) -> str:
    counts = {c: sum(r.category is c for r in results) for c in Category}
    return (
        f"The {len(results)} questions are based on facts in the sample documents: "
        f"{counts[Category.SINGLE_FACT]} single facts (numbers, steps, error codes), "
        f"{counts[Category.CROSS_PAGE_OR_TABLE]} facts that span two pages or sit in a table, "
        f"{counts[Category.CONFUSABLE]} facts that differ between the similar T2 and T3 "
        f"thermostats, and {counts[Category.OUT_OF_SCOPE]} questions the documents do not "
        "answer."
    )


def _bottom_line(
    results: Sequence[QuestionResult],
    metrics: Mapping[str, Any],
    info: RunInfo,
    tuning: Sequence[Mapping[str, Any]] | None = None,
) -> list[str]:
    checks = target_checks(dict(metrics), info.targets)
    evaluated = [c for c in checks if c[3] is not None]
    met = [c for c in evaluated if c[3]]
    in_scope = [r for r in results if r.should_answer]
    out_of_scope = [r for r in results if not r.should_answer]
    answered = sum(r.answered for r in in_scope)
    hits = sum(bool(r.citation_hit) for r in in_scope)
    refused_oos = sum(r.refused for r in out_of_scope)

    lines = []
    if evaluated and len(met) == len(evaluated):
        lines.append(f"**All {len(evaluated)} quality targets were met.**")
    else:
        missed = ", ".join(METRIC_LABELS[c[0]] for c in evaluated if not c[3])
        lines.append(
            f"**{len(met)} of {len(evaluated)} quality targets were met** (missed: {missed}); "
            "see the failure analysis below."
        )
    lines.append(
        f"Of the {len(in_scope)} questions whose answer is in the documents, the assistant "
        f"answered {answered} and cited the correct document and page for {hits} "
        f"({fmt_metric('citation_hit_rate', metrics.get('citation_hit_rate'))})."
    )
    if out_of_scope:
        verdict = (
            "it never invented an answer"
            if refused_oos == len(out_of_scope)
            else f"it answered {len(out_of_scope) - refused_oos} of them, which must be fixed"
        )
        lines.append(
            f"It declined {refused_oos} of {len(out_of_scope)} questions that the documents do "
            f'not cover (for example "{out_of_scope[0].question}"): {verdict}.'
        )
    key_facts = [r for r in in_scope if r.key_facts_ok is not None]
    if key_facts:
        complete = sum(bool(r.key_facts_ok) for r in key_facts)
        missing = [r.id for r in key_facts if not r.key_facts_ok]
        lines.append(
            f"{complete} of {len(key_facts)} answers contain every key fact of the reference "
            "answer" + (f"; incomplete: {', '.join(missing)}." if missing else ".")
        )
    faith = metrics.get("faithfulness")
    if faith is not None:
        lines.append(
            f"On average {faith:.0%} of the statements in an answer are directly supported by "
            "the quoted source passages (RAGAS faithfulness)."
        )
    judge_only = [r.id for r in results if is_judge_only(r)]
    if judge_only:
        flagged = sum(not r.passed for r in results)
        one = len(judge_only) == 1
        lines.append(
            f"{len(judge_only)} of the {flagged} flagged question{'' if flagged == 1 else 's'} "
            f"({', '.join(judge_only)}) {'was' if one else 'were'} flagged only by the "
            f"automatic faithfulness judge; {'its' if one else 'their'} citation and key facts "
            "are correct (see the failure analysis)."
        )
    latency = metrics.get("avg_latency_ms")
    cost = metrics.get("avg_cost_usd")
    if latency is not None and cost is not None:
        lines.append(
            f"An answer takes {latency / 1000:.1f} s on average and costs about "
            f"${cost:.4f} in API fees (about ${cost * 1000:.2f} per 1,000 questions)."
        )
    if tuning:
        lines.append(
            f"{len(tuning)} combinations of chunk size, number of retrieved passages and "
            f"relevance threshold were tested; the chosen settings are "
            f"{_config_text(info.config)} (see Tuning below for the trade-offs)."
        )
    return lines


def _scorecard(metrics: Mapping[str, Any], info: RunInfo) -> list[str]:
    lines = [
        "| Metric | What it measures | Result | Target | Status |",
        "|---|---|---|---|---|",
    ]
    checks = {
        name: (target, met) for name, _, target, met in target_checks(dict(metrics), info.targets)
    }
    for name in (
        "faithfulness",
        "citation_hit_rate",
        "out_of_scope_refusal_rate",
        "false_refusal_rate",
        "key_fact_accuracy",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "retrieval_hit_rate",
    ):
        target, met = checks.get(name, ("-", None))
        status = _status(met) if name in checks else "-"
        lines.append(
            f"| {METRIC_LABELS[name]} | {METRIC_MEANINGS[name]} | "
            f"{fmt_metric(name, metrics.get(name))} | {target} | {status} |"
        )
    for name in ("avg_latency_ms", "p95_latency_ms", "avg_cost_usd"):
        lines.append(
            f"| {METRIC_LABELS[name]} | - | {fmt_metric(name, metrics.get(name))} | - | - |"
        )
    return lines


def _by_category(results: Sequence[QuestionResult]) -> list[str]:
    lines = [
        "| Question type | Questions | Passed | Correct citation | Refused |",
        "|---|---|---|---|---|",
    ]
    for category in Category:
        group = [r for r in results if r.category is category]
        if not group:
            continue
        hits = (
            f"{sum(bool(r.citation_hit) for r in group)}/{len(group)}"
            if category is not Category.OUT_OF_SCOPE
            else "-"
        )
        lines.append(
            f"| {CATEGORY_LABELS[category]} | {len(group)} | "
            f"{sum(r.passed for r in group)}/{len(group)} | {hits} | "
            f"{sum(r.refused for r in group)}/{len(group)} |"
        )
    return lines


def _comparison(
    comparison: Mapping[str, Any], metrics: Mapping[str, Any], info: RunInfo
) -> list[str]:
    other = comparison.get("metrics", {})
    label = _cell(comparison.get("label") or "Other run")
    other_config = _config_text(comparison.get("config", {}))
    lines = [
        f"| Metric | This run (chosen settings) | {label} |",
        "|---|---|---|",
        f"| Settings | {_config_text(info.config)} | {other_config} |",
    ]
    for name in (
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "citation_hit_rate",
        "key_fact_accuracy",
        "out_of_scope_refusal_rate",
        "false_refusal_rate",
        "retrieval_hit_rate",
        "avg_latency_ms",
        "avg_cost_usd",
    ):
        lines.append(
            f"| {METRIC_LABELS[name]} | {fmt_metric(name, metrics.get(name))} | "
            f"{fmt_metric(name, other.get(name))} |"
        )
    return lines


def _config_text(config: Mapping[str, Any]) -> str:
    if not config:
        return "n/a"
    return (
        f"chunk {config.get('chunk_size')}/{config.get('chunk_overlap')} tokens, "
        f"top-k {config.get('top_k')}, threshold {_num(config.get('threshold')) or 0:.2f}"
    )


TUNING_TABLE_METRICS = (
    "citation_hit_rate",
    "key_fact_accuracy",
    "out_of_scope_refusal_rate",
    "false_refusal_rate",
    "retrieval_hit_rate",
    "avg_latency_ms",
    "avg_cost_usd",
)


def _tuning_table(rows: Sequence[Mapping[str, Any]], info: RunInfo) -> list[str]:
    lines = [
        "| Chunk size / overlap | Top-k | Threshold | Runs | Correct citation | Key facts "
        "| Out-of-scope refused | False refusals | Retrieval hit | Avg latency | Avg cost "
        "| Failed questions |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        is_final = (
            int(row["chunk_size"]) == info.config["chunk_size"]
            and int(row["chunk_overlap"]) == info.config["chunk_overlap"]
            and int(row["top_k"]) == info.config["top_k"]
            and abs(float(row["threshold"]) - float(info.config["threshold"])) < 1e-9
        )
        marker = " **(final)**" if is_final else ""
        cells = [
            f"{row['chunk_size']} / {row['chunk_overlap']}{marker}",
            str(row["top_k"]),
            f"{float(row['threshold']):.2f}",
            str(int(_num(row.get("runs")) or 1)),
            *(fmt_metric(name, _num(row.get(name))) for name in TUNING_TABLE_METRICS),
            _text(row.get("failed_questions")),
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _text(value: Any) -> str:
    """A non-empty string cell, or "-" (CSV round-trips turn empty cells into NaN)."""
    return _cell(value) if isinstance(value, str) and value.strip() else "-"


def _num(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if number != number else number  # NaN check


def _failure_section(results: Sequence[QuestionResult]) -> list[str]:
    failures = [r for r in results if not r.passed]
    lines: list[str] = []
    if not failures:
        lines.append("No question failed in this run.")
        return lines
    for r in failures:
        lines += [
            f"**{r.id} ({CATEGORY_LABELS[r.category]}): {r.question}**",
            "",
            f"- What went wrong: {r.diagnosis_detail}",
            *([f"- Note: {JUDGE_ONLY_NOTE}"] if is_judge_only(r) else []),
            f"- Expected source: {'; '.join(r.expected_sources) or 'none (should refuse)'}",
            f'- Assistant\'s answer: "{_short(r.answer, 300)}"',
            f"- Cited: {_pages(r.cited_sources)}",
            "- Top retrieved: "
            + (
                "; ".join(f"{c.label} ({c.score:.2f})" for c in r.retrieved[:3])
                if r.retrieved
                else "none"
            ),
            "",
        ]
    return lines


# Question ids as used in eval/questions.yaml, e.g. "SF-01", "CP-03", "OOS-05".
_QUESTION_ID = re.compile(r"\b[A-Z]{2,4}-\d{2}\b")

JUDGE_ONLY_NOTE = (
    "Flagged by the automatic judge only: the correct page was cited and every key fact is "
    "in the answer. Check it by hand before treating it as a real error."
)


def is_judge_only(result: QuestionResult) -> bool:
    """True if the failure comes only from the RAGAS judge, not from a deterministic check.

    `diagnose()` reports low faithfulness only after the citation and key fact checks passed.
    """
    return result.diagnosis is Diagnosis.LOW_FAITHFULNESS


def reviewed_ids(review_notes: str) -> set[str]:
    """Question ids mentioned in the hand-written review notes."""
    return set(_QUESTION_ID.findall(review_notes))


def _review_section(results: Sequence[QuestionResult], review_notes: str) -> list[str]:
    """Hand-written review notes, plus a warning for failures they do not cover.

    The notes are written once and describe failure patterns seen across runs, while the
    rest of the report is generated from the current run. Any failure of this run whose
    question id does not appear in the notes is listed as not yet reviewed by hand.
    """
    lines = [
        "_Known failure patterns, checked by hand against the PDFs over several evaluation "
        "runs. Answers vary slightly between runs, so not every pattern appears in every "
        "run._",
        "",
        review_notes.strip(),
        "",
    ]
    covered = reviewed_ids(review_notes)
    unreviewed = [r for r in results if not r.passed and r.id not in covered]
    if unreviewed:
        items = ", ".join(
            f"{r.id} ({r.diagnosis.value.replace('_', ' ')}"
            + (", judge only" if is_judge_only(r) else "")
            + ")"
            for r in unreviewed
        )
        lines += [
            f"**Not yet reviewed by hand: {items}.** These failures are not covered by the "
            "notes above; only the automatic diagnosis in the failure analysis applies to "
            "them until someone checks the answers against the documents.",
            "",
        ]
    return lines


def _risk_section(results: Sequence[QuestionResult], threshold: float) -> list[str]:
    """Near misses worth knowing about even when every question passed."""
    lines: list[str] = []
    oos_reaching_model = [
        r
        for r in results
        if not r.should_answer and r.top_score is not None and r.top_score >= threshold
    ]
    if oos_reaching_model:
        ids = ", ".join(f"{r.id} ({r.top_score:.2f})" for r in oos_reaching_model)
        lines.append(
            f"- {len(oos_reaching_model)} of {sum(not r.should_answer for r in results)} "
            f"out-of-scope questions scored above the relevance threshold ({threshold:.2f}) and "
            f"were stopped by the model's own refusal, not by the threshold: {ids}. These "
            "questions sound like real support topics, so the second safety layer matters."
        )
    in_scope = [r for r in results if r.should_answer and r.retrieved]
    if in_scope:
        weakest = min(in_scope, key=lambda r: r.top_score or 0.0)
        lines.append(
            f"- The weakest in-scope match was {weakest.id} (best score "
            f"{weakest.top_score:.2f}, threshold {threshold:.2f}). A higher threshold would "
            "start refusing questions like this one."
        )
    late = [r for r in results if r.should_answer and (r.expected_rank or 0) > 3]
    if late:
        ids = ", ".join(f"{r.id} (rank {r.expected_rank})" for r in late)
        lines.append(
            f"- For {ids} the page with the answer was ranked below the top 3 passages; a "
            "smaller top-k would lose these answers."
        )
    for name, label in (
        ("context_precision", "context precision"),
        ("context_recall", "context recall"),
    ):
        low = [r for r in results if (r.scores.get(name) is not None and r.scores[name] < 0.5)]
        if low:
            ids = ", ".join(f"{r.id} ({r.scores[name]:.2f})" for r in low)
            lines.append(f"- Low {label} (below 0.50): {ids}.")
    return lines


def _recommendations(results: Sequence[QuestionResult]) -> list[str]:
    seen: list[Diagnosis] = []
    for r in results:
        if not r.passed and r.diagnosis not in seen:
            seen.append(r.diagnosis)
    items = [RECOMMENDATIONS[d] for d in seen if d in RECOMMENDATIONS]
    items += list(GENERAL_RECOMMENDATIONS)
    return [f"{i}. {text}" for i, text in enumerate(items, start=1)]


def _details_table(results: Sequence[QuestionResult]) -> list[str]:
    lines = [
        "| ID | Question | Outcome | Cited | Key facts | Top score | Faith. | Relev. | Ctx prec. "
        "| Ctx rec. | Latency | Cost |",
        "|---|---|---|---|---|---|---|---|---|---|---|---|",
    ]
    for r in results:
        top = f"{r.top_score:.2f}" if r.top_score is not None else "-"
        cells = [
            r.id,
            _cell(r.question),
            _outcome(r),
            _cell(_pages(r.cited_sources)),
            _key_facts_cell(r),
            top,
            *(_score(r, name) for name in RAGAS_METRICS),
            f"{r.latency_ms / 1000:.1f} s",
            f"${r.cost_usd:.5f}",
        ]
        lines.append("| " + " | ".join(cells) + " |")
    return lines


def _key_facts_cell(result: QuestionResult) -> str:
    if result.key_facts_ok is None:
        return "-"
    found = len(result.key_facts) - len(result.missing_key_facts)
    return f"{found}/{len(result.key_facts)}"


def _answers_section(results: Sequence[QuestionResult]) -> list[str]:
    lines = []
    for r in results:
        lines += [
            f"**{r.id}. {r.question}**",
            "",
            f"- Answer: {_short(r.answer, 600)}",
            f"- Reference: {_short(r.ground_truth, 600)}",
            "",
        ]
    return lines


def render_summary(
    results: Sequence[QuestionResult],
    metrics: Mapping[str, Any],
    info: RunInfo,
    *,
    comparison: Mapping[str, Any] | None = None,
    tuning: Sequence[Mapping[str, Any]] | None = None,
    tuning_notes: str | None = None,
    review_notes: str | None = None,
) -> str:
    """Render summary.md.

    `tuning_notes` and `review_notes` are hand-written Markdown (eval/notes/*.md) placed at
    the top of the tuning section and under the failure analysis.
    """
    threshold = float(info.config["threshold"])
    out: list[str] = [
        "# Evaluation Summary: Lumora Document Assistant",
        "",
        f"_Generated {info.generated_at} by `make eval` - {len(results)} questions - chat "
        f"model `{info.chat_model}` - {_config_text(info.config)}._",
        "",
        "## Bottom line",
        "",
        *[f"- {line}" for line in _bottom_line(results, metrics, info, tuning)],
        "",
        "## Scorecard",
        "",
        *_scorecard(metrics, info),
        "",
        "## Results by question type",
        "",
        _mix_text(results),
        "",
        *_by_category(results),
        "",
    ]

    if comparison or tuning or tuning_notes:
        out += ["## Tuning", ""]
        if tuning_notes:
            out += [tuning_notes.strip(), ""]
        if comparison:
            out += [
                "Full evaluation (including RAGAS) of the chosen settings next to the "
                "closest alternative:",
                "",
                *_comparison(comparison, metrics, info),
                "",
            ]
        if tuning:
            out += [
                f"<details><summary>Full parameter sweep ({len(tuning)} configurations, custom "
                "metrics only)</summary>",
                "",
                f"Same {len(results)} questions; 4 questions run in parallel, so latencies are "
                "higher than in a single-user run. 'Runs' > 1 means the configuration was "
                "repeated and the metrics are averages; failed questions show how often they "
                "failed.",
                "",
                *_tuning_table(tuning, info),
                "",
                "</details>",
                "",
            ]

    out += [
        "## Failure analysis",
        "",
        *_failure_section(results),
        "",
    ]
    if review_notes:
        out += ["### Manual review", "", *_review_section(results, review_notes)]
    risks = _risk_section(results, threshold)
    if risks:
        out += ["### Risks and near misses", "", *risks, ""]

    out += [
        "## Recommendations",
        "",
        *_recommendations(results),
        "",
        "## Per-question details",
        "",
        *_details_table(results),
        "",
        "Faith. = faithfulness, Relev. = answer relevancy, Ctx prec. / Ctx rec. = context "
        "precision / recall (RAGAS, 0-1; '-' = not scored, e.g. refusals). Top score = cosine "
        "similarity of the best retrieved passage.",
        "",
        "<details><summary>Answers next to the reference answers</summary>",
        "",
        *_answers_section(results),
        "</details>",
        "",
        "## Method",
        "",
        "- Every question is sent to the same `answer_question()` function the API uses "
        "(no HTTP), one at a time, so latency is end-to-end for one request.",
        "- **Citation hit**: an in-scope answer counts as correct when its sources include "
        "at least one expected document page (`expected_sources` in `eval/questions.yaml`). "
        "A refusal counts as a miss.",
        "- **Refusal rates**: out-of-scope refusal rate = refused / out-of-scope questions; "
        "false refusal rate = refused / in-scope questions.",
        "- **RAGAS** (v0.4) scores in-scope questions only, using "
        f"`{info.judge_model or info.chat_model}` as the judge. Faithfulness and answer "
        "relevancy are not scored for refusals (a refusal makes no claims)."
        if info.ragas
        else "- RAGAS scoring was skipped for this run (`--no-ragas`).",
        "- **Cost** = chat tokens (question rewrite and answer) + query embedding tokens, at "
        f"${info.pricing.chat_input_per_m:.2f} / ${info.pricing.chat_output_per_m:.2f} per 1M "
        f"input / output tokens and ${info.pricing.embedding_per_m:.2f} per 1M embedding "
        "tokens. Evaluation (judge) calls are not included.",
        "- Raw data: `eval/reports/results.csv` (one row per question) and "
        "`eval/reports/metrics.json`.",
        "- Reproduce: `make ingest && make eval`. Parameter sweep: `make eval-tune`.",
        "",
    ]
    return "\n".join(out)


def write_reports(
    out_dir: Path,
    results: Sequence[QuestionResult],
    metrics: Mapping[str, Any],
    info: RunInfo,
    *,
    comparison: Mapping[str, Any] | None = None,
    tuning: Sequence[Mapping[str, Any]] | None = None,
    tuning_notes: str | None = None,
    review_notes: str | None = None,
) -> dict[str, Path]:
    """Write results.csv, results.json, metrics.json and summary.md into `out_dir`.

    results.json keeps every field of every result so that `load_run()` can re-render
    summary.md later without new API calls.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    paths = {
        "results": out_dir / "results.csv",
        "raw": out_dir / "results.json",
        "metrics": out_dir / "metrics.json",
        "summary": out_dir / "summary.md",
    }
    results_frame(results).to_csv(paths["results"], index=False)
    paths["raw"].write_text(
        json.dumps([r.model_dump(mode="json") for r in results], indent=1, ensure_ascii=False)
        + "\n",
        encoding="utf-8",
    )
    paths["metrics"].write_text(
        json.dumps(metrics_document(metrics, info), indent=2) + "\n", encoding="utf-8"
    )
    write_summary(
        paths["summary"],
        results,
        metrics,
        info,
        comparison=comparison,
        tuning=tuning,
        tuning_notes=tuning_notes,
        review_notes=review_notes,
    )
    return paths


def write_summary(
    path: Path,
    results: Sequence[QuestionResult],
    metrics: Mapping[str, Any],
    info: RunInfo,
    *,
    comparison: Mapping[str, Any] | None = None,
    tuning: Sequence[Mapping[str, Any]] | None = None,
    tuning_notes: str | None = None,
    review_notes: str | None = None,
) -> None:
    path.write_text(
        render_summary(
            results,
            metrics,
            info,
            comparison=comparison,
            tuning=tuning,
            tuning_notes=tuning_notes,
            review_notes=review_notes,
        ),
        encoding="utf-8",
    )


def load_run(out_dir: Path) -> tuple[list[QuestionResult], RunInfo]:
    """Load the results and run info written by `write_reports()`."""
    raw = json.loads((out_dir / "results.json").read_text(encoding="utf-8"))
    document = json.loads((out_dir / "metrics.json").read_text(encoding="utf-8"))
    models = document.get("models", {})
    info = RunInfo(
        generated_at=document["generated_at"],
        config=document["config"],
        chat_model=models.get("chat", ""),
        embedding_model=models.get("embedding", ""),
        judge_model=models.get("judge"),
        pricing=Pricing(**document.get("pricing_usd_per_1m_tokens", {})),
        targets=Targets(**document.get("targets", {})),
        ragas=bool(document.get("ragas", True)),
        label=document.get("label"),
    )
    return [QuestionResult.model_validate(item) for item in raw], info


def load_tuning(path: Path) -> list[dict[str, Any]] | None:
    if not path.is_file():
        return None
    frame = pd.read_csv(path)
    return frame.to_dict(orient="records") if not frame.empty else None


def load_comparison(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    return json.loads(path.read_text(encoding="utf-8"))
