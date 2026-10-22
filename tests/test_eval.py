"""Evaluation suite: question set, custom metrics, diagnosis, reports (no API calls)."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any

import pymupdf
import pytest
from langchain_core.documents import Document

from app.config import Settings
from app.rag.schemas import ChatResult, Source
from app.retrieval.retriever import RetrievedChunk
from eval import ragas_scoring, runner
from eval.dataset import Category, EvalQuestion, load_questions
from eval.metrics import (
    Diagnosis,
    Pricing,
    QuestionResult,
    RetrievedPage,
    Targets,
    aggregate,
    contains_fact,
    diagnose,
    target_checks,
)
from eval.report import RunInfo, load_run, load_tuning, render_summary, write_reports
from eval.tune import _chunkings, build_grid, merge_runs, summarize_runs
from scripts.check_retrieval import parse_facts

ROOT = Path(__file__).resolve().parent.parent
PDF_DIR = ROOT / "data" / "pdfs"
T2 = "Product Guide - Lumora Thermostat T2.pdf"
T3 = "Product Guide - Lumora Thermostat T3.pdf"


# --------------------------------------------------------------------------- question set


def test_question_set_has_the_required_mix() -> None:
    questions = load_questions()
    counts = {c: sum(q.category is c for q in questions) for c in Category}
    assert len(questions) == 20
    assert counts == {
        Category.SINGLE_FACT: 10,
        Category.CROSS_PAGE_OR_TABLE: 3,
        Category.CONFUSABLE: 2,
        Category.OUT_OF_SCOPE: 5,
    }
    assert len({q.id for q in questions}) == 20


def test_expected_sources_exist_in_the_sample_pdfs() -> None:
    for question in load_questions():
        for source in question.expected_sources:
            path = PDF_DIR / source.document
            assert path.is_file(), f"{question.id}: missing {source.document}"
            with pymupdf.open(path) as pdf:
                assert all(1 <= p <= pdf.page_count for p in source.pages), question.id


def test_fact_ids_match_facts_md_file_and_pages() -> None:
    facts = parse_facts(PDF_DIR / "FACTS.md")
    for question in load_questions():
        if question.should_answer:
            assert question.fact_ids, f"{question.id}: in-scope questions cite a fact"
        expected = question.expected_pages()
        for fact_id in question.fact_ids:
            fact = facts[fact_id]
            assert {(fact.source, p) for p in fact.pages} <= expected, (question.id, fact_id)


def test_key_facts_appear_in_the_ground_truth() -> None:
    for question in load_questions():
        for fact in question.key_facts:
            assert contains_fact(question.ground_truth, fact), (question.id, fact)


def _question(**overrides: Any) -> dict[str, Any]:
    data: dict[str, Any] = {
        "id": "Q1",
        "category": "single_fact",
        "question": "q?",
        "ground_truth": "a",
        "expected_sources": [{"document": "Doc.pdf", "pages": [1]}],
        "should_answer": True,
    }
    data.update(overrides)
    return data


@pytest.mark.parametrize(
    "overrides",
    [
        {"expected_sources": []},
        {"category": "out_of_scope", "should_answer": False},
        {"category": "single_fact", "should_answer": False, "expected_sources": []},
        {
            "category": "out_of_scope",
            "should_answer": False,
            "expected_sources": [],
            "key_facts": ["x"],
        },
    ],
)
def test_inconsistent_questions_are_rejected(overrides: dict[str, Any]) -> None:
    with pytest.raises(ValueError):
        EvalQuestion.model_validate(_question(**overrides))


def test_duplicate_question_ids_are_rejected(tmp_path: Path) -> None:
    import yaml

    path = tmp_path / "q.yaml"
    path.write_text(yaml.safe_dump({"questions": [_question(), _question()]}))
    with pytest.raises(ValueError, match="duplicate"):
        load_questions(path)


# --------------------------------------------------------------------------- metrics


def test_contains_fact_is_case_comma_and_alternative_insensitive() -> None:
    answer = "Refunds above $5,000.00 need the Finance   Controller."
    assert contains_fact(answer, "$5000")
    assert contains_fact(answer, "finance controller")
    assert contains_fact(answer, "Team Lead|Finance Controller")
    assert not contains_fact(answer, "Team Lead")


def make_result(
    *,
    should_answer: bool = True,
    answered: bool = True,
    cited: list[tuple[str, int]] | None = None,
    retrieved: list[RetrievedPage] | None = None,
    answer: str = "Hold the control ring for 12 seconds.",
    key_facts: list[str] | None = None,
    scores: dict[str, float | None] | None = None,
    error: str | None = None,
) -> QuestionResult:
    question = EvalQuestion(
        id="Q",
        category=Category.SINGLE_FACT if should_answer else Category.OUT_OF_SCOPE,
        question="How do I reset the T2?",
        ground_truth="Hold the control ring for 12 seconds.",
        expected_sources=[{"document": T2, "pages": [5]}] if should_answer else [],
        should_answer=should_answer,
        key_facts=(key_facts if key_facts is not None else ["12 seconds"]) if should_answer else [],
    )
    result = QuestionResult.for_question(question)
    result.answered = answered
    result.answer = answer if answered else "I'm sorry, ..."
    result.cited_sources = cited if cited is not None else ([(T2, 5)] if answered else [])
    result.retrieved = (
        retrieved
        if retrieved is not None
        else [RetrievedPage(document=T2, page=5, score=0.7, in_context=True)]
    )
    result.scores = scores or {}
    result.error = error
    return result


def page(document: str, number: int, score: float, in_context: bool = True) -> RetrievedPage:
    return RetrievedPage(document=document, page=number, score=score, in_context=in_context)


@pytest.mark.parametrize(
    ("kwargs", "expected"),
    [
        ({}, Diagnosis.OK),
        ({"error": "boom"}, Diagnosis.ERROR),
        ({"answered": False, "retrieved": [page(T3, 5, 0.6)]}, Diagnosis.RETRIEVAL_MISS),
        ({"answered": False, "retrieved": [page(T2, 5, 0.3, False)]}, Diagnosis.BELOW_THRESHOLD),
        ({"answered": False, "retrieved": [page(T2, 5, 0.5, False)]}, Diagnosis.CONTEXT_BUDGET),
        ({"answered": False}, Diagnosis.MODEL_DECLINED),
        (
            {"cited": [(T3, 5)], "retrieved": [page(T3, 5, 0.6), page(T2, 5, 0.5, False)]},
            Diagnosis.WRONG_SOURCE,
        ),
        ({"cited": [(T3, 5)], "retrieved": [page(T2, 5, 0.6)]}, Diagnosis.CITATION_MISS),
        ({"answer": "Hold it for 5 seconds."}, Diagnosis.MISSING_KEY_FACTS),
        ({"scores": {"faithfulness": 0.5}}, Diagnosis.LOW_FAITHFULNESS),
        ({"should_answer": False, "answered": False}, Diagnosis.OK),
        ({"should_answer": False, "cited": [(T3, 1)]}, Diagnosis.ANSWERED_OUT_OF_SCOPE),
    ],
)
def test_diagnose(kwargs: dict[str, Any], expected: Diagnosis) -> None:
    diagnosis, detail = diagnose(make_result(**kwargs), threshold=0.35)
    assert diagnosis is expected
    assert detail


def test_aggregate_rates_and_targets() -> None:
    results = [
        make_result(scores={"faithfulness": 1.0}),
        make_result(cited=[(T3, 1)], scores={"faithfulness": 0.8}),
        make_result(answered=False),
        make_result(answered=False, retrieved=[]),
        make_result(should_answer=False, answered=False),
        make_result(should_answer=False, cited=[(T3, 1)]),
    ]
    for r in results:
        r.latency_ms = 1000
        r.cost_usd = 0.001
        r.diagnosis, r.diagnosis_detail = diagnose(r, 0.35)
    metrics = aggregate(results)

    assert metrics["citation_hit_rate"] == pytest.approx(1 / 4)
    assert metrics["key_fact_accuracy"] == pytest.approx(2 / 4)
    assert metrics["false_refusal_rate"] == pytest.approx(2 / 4)
    assert metrics["out_of_scope_refusal_rate"] == pytest.approx(1 / 2)
    assert metrics["retrieval_hit_rate"] == pytest.approx(3 / 4)
    assert metrics["faithfulness"] == pytest.approx(0.9)
    assert metrics["faithfulness_count"] == 2
    assert metrics["avg_latency_ms"] == 1000
    assert metrics["passed"] == 2

    checks = {name: met for name, _, _, met in target_checks(metrics, Targets())}
    assert checks == {
        "faithfulness": True,
        "citation_hit_rate": False,
        "out_of_scope_refusal_rate": False,
        "false_refusal_rate": False,
    }


def test_pricing_cost() -> None:
    pricing = Pricing(chat_input_per_m=1.0, chat_output_per_m=2.0, embedding_per_m=0.5)
    assert pricing.cost(1_000_000, 500_000, 2_000_000) == pytest.approx(3.0)


# --------------------------------------------------------------------------- runner


def _settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        chroma_persist_dir=tmp_path / "chroma",
        retrieval_score_threshold=0.35,
        retrieval_top_k=3,
    )


def _chunk(document: str, number: int, score: float, text: str) -> RetrievedChunk:
    metadata = {"source": document, "page": number, "chunk_id": f"{document}-{number}"}
    return RetrievedChunk(doc=Document(page_content=text, metadata=metadata), score=score)


def test_run_question_records_answer_retrieval_and_cost(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    question = load_questions()[2]  # SF-03, T2 factory reset (p.5)
    chat = ChatResult(
        answer="Hold the control ring for 12 seconds until RESET shows.",
        is_answerable=True,
        sources=[
            Source(document=T2, page=5, snippet="...", score=0.7, chunk_id="t2-5"),
        ],
        model="m",
        latency_ms=1234,
        standalone_question=question.question,
        contexts=["page five text"],
    )
    monkeypatch.setattr(runner, "answer_question", lambda *a, **k: chat)
    monkeypatch.setattr(
        runner,
        "retrieve",
        lambda *a, **k: [_chunk(T2, 5, 0.7, "page five text"), _chunk(T3, 5, 0.6, "other")],
    )
    result = runner.run_question(
        question, _settings(tmp_path), store=None, llm=None, pricing=Pricing()
    )

    assert result.answered and result.citation_hit and result.key_facts_ok
    assert result.latency_ms == 1234
    assert [(c.label, c.in_context) for c in result.retrieved] == [
        (f"{T2} p.5", True),
        (f"{T3} p.5", False),
    ]
    assert result.expected_rank == 1
    assert result.embedding_tokens > 0
    assert result.cost_usd == pytest.approx(Pricing().cost(0, 0, result.embedding_tokens))


def test_run_question_records_errors(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(*_: Any, **__: Any) -> ChatResult:
        raise TimeoutError("slow")

    monkeypatch.setattr(runner, "answer_question", boom)
    result = runner.run_question(
        load_questions()[0], _settings(tmp_path), store=None, llm=None, pricing=Pricing()
    )
    assert result.error == "TimeoutError: slow"
    assert diagnose(result, 0.35)[0] is Diagnosis.ERROR


def test_settings_for_uses_a_separate_collection_for_other_chunking(tmp_path: Path) -> None:
    base = _settings(tmp_path)
    same = runner.settings_for(base, runner.EvalConfig(4, 0.3, 500, 80))
    other = runner.settings_for(base, runner.EvalConfig(4, 0.3, 300, 50))
    assert same.chroma_collection == base.chroma_collection
    assert (same.retrieval_top_k, same.retrieval_score_threshold) == (4, 0.3)
    assert other.chroma_collection == f"{base.chroma_collection}_eval_cs300_ov50"
    assert other.chunk_size_tokens == 300
    with pytest.raises(ValueError):
        runner.settings_for(base, runner.EvalConfig(4, 0.3, 100, 100))


def test_tuning_grid() -> None:
    assert _chunkings("300:50, 500:80") == [(300, 50), (500, 80)]
    grid = build_grid([(300, 50)], [3, 6], [0.3, 0.4])
    assert [(c.top_k, c.threshold) for c in grid] == [(3, 0.3), (3, 0.4), (6, 0.3), (6, 0.4)]


# --------------------------------------------------------------------------- ragas scoring


class FakeMetric:
    def __init__(self, value: float | Exception) -> None:
        self.value = value
        self.calls: list[dict[str, Any]] = []

    async def ascore(self, **kwargs: Any) -> Any:
        self.calls.append(kwargs)
        if isinstance(self.value, Exception):
            raise self.value
        return type("MetricResult", (), {"value": self.value})()


def test_score_results_skips_refusals_and_records_errors(tmp_path: Path) -> None:
    scorers = ragas_scoring.RagasScorers(
        faithfulness=FakeMetric(0.9),
        answer_relevancy=FakeMetric(RuntimeError("judge failed")),
        context_precision=FakeMetric(0.5),
        context_recall=FakeMetric(1.0),
    )
    answered = make_result()
    answered.contexts = ["ctx"]
    refused_with_context = make_result(answered=False)
    refused_with_context.contexts = ["ctx"]
    refused_empty = make_result(answered=False)
    out_of_scope = make_result(should_answer=False, answered=False)

    ragas_scoring.score_results(
        [answered, refused_with_context, refused_empty, out_of_scope],
        _settings(tmp_path),
        scorers=scorers,
    )

    assert answered.scores == {
        "faithfulness": 0.9,
        "answer_relevancy": None,
        "context_precision": 0.5,
        "context_recall": 1.0,
    }
    assert "judge failed" in answered.score_errors["answer_relevancy"]
    assert refused_with_context.scores == {"context_precision": 0.5, "context_recall": 1.0}
    assert refused_empty.scores == {"context_precision": 0.0, "context_recall": 0.0}
    assert out_of_scope.scores == {}
    assert len(scorers.faithfulness.calls) == 1
    assert scorers.context_recall.calls[0]["reference"] == answered.ground_truth


# --------------------------------------------------------------------------- reports


def _info() -> RunInfo:
    return RunInfo(
        generated_at="2026-01-01T00:00:00+00:00",
        config={
            "chunk_size": 500,
            "chunk_overlap": 80,
            "top_k": 6,
            "threshold": 0.35,
            "collection": "c",
            "max_context_tokens": 3000,
        },
        chat_model="gpt-4o-mini",
        embedding_model="text-embedding-3-small",
        judge_model="gpt-4o-mini",
        pricing=Pricing(),
    )


def _results() -> list[QuestionResult]:
    results = [
        make_result(scores={"faithfulness": 1.0}),
        make_result(cited=[(T3, 1)]),
        make_result(should_answer=False, answered=False),
    ]
    for r in results:
        r.diagnosis, r.diagnosis_detail = diagnose(r, 0.35)
    return results


def test_summary_puts_conclusions_before_data_and_explains_failures() -> None:
    results = _results()
    text = render_summary(
        results,
        aggregate(results),
        _info(),
        comparison={
            "label": "Candidate",
            "config": {"chunk_size": 500, "top_k": 8},
            "metrics": {"avg_cost_usd": 0.1},
        },
        tuning=[
            {
                "chunk_size": 500,
                "chunk_overlap": 80,
                "top_k": 6,
                "threshold": 0.35,
                "citation_hit_rate": 1.0,
                "failed_questions": float("nan"),
            }
        ],
        tuning_notes="We tuned things.",
        review_notes="Checked by hand.",
    )
    order = [
        "## Bottom line",
        "## Scorecard",
        "## Tuning",
        "We tuned things.",
        "## Failure analysis",
        "### Manual review",
        "## Recommendations",
        "## Per-question details",
        "## Method",
    ]
    positions = [text.index(heading) for heading in order]
    assert positions == sorted(positions)
    assert "Not met" in text  # citation hit rate 50%
    assert "but the answer cited" in text  # citation miss explained
    assert "**(final)**" in text
    assert "| nan |" not in text


def test_write_reports_creates_csv_json_and_summary(tmp_path: Path) -> None:
    results = _results()
    paths = write_reports(tmp_path, results, aggregate(results), _info())
    assert {p.name for p in paths.values()} == {
        "results.csv",
        "results.json",
        "metrics.json",
        "summary.md",
    }
    loaded, info = load_run(tmp_path)
    assert [r.model_dump() for r in loaded] == [r.model_dump() for r in results]
    assert info == _info()
    import pandas as pd

    frame = pd.read_csv(paths["results"])
    assert list(frame["id"]) == ["Q", "Q", "Q"]
    assert {"citation_hit", "key_facts_ok", "faithfulness", "cost_usd"} <= set(frame.columns)
    assert load_tuning(tmp_path / "missing.csv") is None


def test_ragas_metric_failure_does_not_raise() -> None:
    value, error = asyncio.run(
        ragas_scoring._score_one(
            "faithfulness", FakeMetric(ValueError("bad")), {}, asyncio.Semaphore(1)
        )
    )
    assert value is None and "bad" in error


def test_merge_runs_replaces_rerun_configs_and_sorts() -> None:
    import pandas as pd

    def row(threshold: float, passed: int) -> dict[str, Any]:
        config = {"chunk_size": 500, "chunk_overlap": 80, "top_k": 6, "threshold": threshold}
        return {**config, "passed": passed}

    merged = merge_runs(pd.DataFrame([row(0.4, 18), row(0.3, 17)]), pd.DataFrame([row(0.4, 20)]))
    assert list(zip(merged["threshold"], merged["passed"], strict=True)) == [(0.3, 17), (0.4, 20)]


def test_summarize_runs_averages_metrics_and_counts_failures() -> None:
    summary = summarize_runs(
        [{"passed": 19, "avg_cost_usd": 0.002}, {"passed": 20, "avg_cost_usd": 0.004}],
        [["SF-01"], []],
    )
    assert summary["runs"] == 2
    assert summary["passed"] == pytest.approx(19.5)
    assert summary["avg_cost_usd"] == pytest.approx(0.003)
    assert summary["failed_questions"] == "SF-01 (1/2)"
    assert summarize_runs([{"passed": 18}], [["A", "B"]])["failed_questions"] == "A B"
