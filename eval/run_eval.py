"""Run the evaluation question set and write reports to eval/reports/.

Each question in eval/questions.yaml is answered by `answer_question()` (no HTTP). The run
computes RAGAS metrics (faithfulness, answer relevancy, context precision, context recall;
in-scope questions only) and custom metrics (citation hit rate, out-of-scope refusal rate,
in-scope false refusal rate, latency, cost), then writes:

    eval/reports/results.csv    one row per question
    eval/reports/metrics.json   aggregate metrics and run configuration
    eval/reports/summary.md     client-facing summary

Requires an indexed vector store (`make ingest`) and makes real API calls.

Usage:
    python -m eval.run_eval                                # settings from .env
    python -m eval.run_eval --top-k 4 --threshold 0.3      # override retrieval parameters
    python -m eval.run_eval --chunk-size 300 --chunk-overlap 50   # separate eval index
    python -m eval.run_eval --no-ragas                     # custom metrics only
    python -m eval.run_eval --render-only                  # rebuild summary.md, no API calls

If eval/reports/comparison/metrics.json (a full run with other settings, e.g. the
runner-up of the parameter sweep) and eval/reports/tuning.csv (from `python -m eval.tune`)
exist, summary.md includes a side-by-side comparison and the parameter sweep.
Hand-written commentary in eval/notes/tuning.md and eval/notes/review.md is included when
present.
"""

from __future__ import annotations

import argparse
import logging
import sys
from collections.abc import Sequence
from datetime import datetime
from pathlib import Path

from app.config import MissingOpenAIKeyError, get_settings
from app.logging_config import configure_logging
from eval.dataset import DEFAULT_QUESTIONS_PATH, load_questions
from eval.metrics import Pricing, Targets, aggregate, target_checks
from eval.report import (
    METRIC_LABELS,
    RunInfo,
    fmt_metric,
    load_comparison,
    load_run,
    load_tuning,
    write_reports,
    write_summary,
)
from eval.runner import (
    EvalConfig,
    IndexNotReadyError,
    prepare_vectorstore,
    rediagnose,
    run_questions,
    settings_for,
)

logger = logging.getLogger(__name__)

EVAL_DIR = Path(__file__).resolve().parent
DEFAULT_OUT_DIR = EVAL_DIR / "reports"
DEFAULT_COMPARISON = DEFAULT_OUT_DIR / "comparison" / "metrics.json"
DEFAULT_TUNING = DEFAULT_OUT_DIR / "tuning.csv"
DEFAULT_NOTES_DIR = EVAL_DIR / "notes"


def add_config_arguments(parser: argparse.ArgumentParser) -> None:
    """CLI flags shared with eval/tune.py: pricing and model options."""
    defaults = Pricing()
    parser.add_argument(
        "--questions", type=Path, default=DEFAULT_QUESTIONS_PATH, help="Question set (YAML)."
    )
    parser.add_argument(
        "--price-input", type=float, default=defaults.chat_input_per_m,
        help="Chat model USD per 1M input tokens.",
    )  # fmt: skip
    parser.add_argument(
        "--price-output", type=float, default=defaults.chat_output_per_m,
        help="Chat model USD per 1M output tokens.",
    )  # fmt: skip
    parser.add_argument(
        "--price-embedding", type=float, default=defaults.embedding_per_m,
        help="Embedding model USD per 1M tokens.",
    )  # fmt: skip
    parser.add_argument("-v", "--verbose", action="store_true", help="Show INFO logs.")


def pricing_from_args(args: argparse.Namespace) -> Pricing:
    return Pricing(
        chat_input_per_m=args.price_input,
        chat_output_per_m=args.price_output,
        embedding_per_m=args.price_embedding,
    )


def _optional_path(value: str) -> Path | None:
    return None if value.lower() in {"", "none"} else Path(value)


def _read_note(directory: Path | None, name: str) -> str | None:
    if directory is None:
        return None
    path = directory / name
    return path.read_text(encoding="utf-8") if path.is_file() else None


def parse_args(argv: Sequence[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_config_arguments(parser)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT_DIR, help="Report directory.")
    parser.add_argument("--top-k", type=int, help="Override RETRIEVAL_TOP_K.")
    parser.add_argument("--threshold", type=float, help="Override RETRIEVAL_SCORE_THRESHOLD.")
    parser.add_argument("--chunk-size", type=int, help="Override CHUNK_SIZE_TOKENS.")
    parser.add_argument("--chunk-overlap", type=int, help="Override CHUNK_OVERLAP_TOKENS.")
    parser.add_argument("--no-ragas", action="store_true", help="Skip RAGAS scoring.")
    parser.add_argument(
        "--judge-model", help="Chat model used by RAGAS as judge (default OPENAI_CHAT_MODEL)."
    )
    parser.add_argument(
        "--concurrency", type=int, default=4, help="Parallel RAGAS metric calls (default 4)."
    )
    parser.add_argument(
        "--comparison", type=_optional_path, default=DEFAULT_COMPARISON,
        help="metrics.json of another run for the side-by-side table ('none' to skip).",
    )  # fmt: skip
    parser.add_argument(
        "--tuning", type=_optional_path, default=DEFAULT_TUNING,
        help="tuning.csv from eval/tune.py ('none' to skip).",
    )  # fmt: skip
    parser.add_argument(
        "--notes-dir", type=_optional_path, default=DEFAULT_NOTES_DIR,
        help="Directory with tuning.md / review.md commentary ('none' to skip).",
    )  # fmt: skip
    parser.add_argument(
        "--label", help="Name of this run, shown when another report compares against it."
    )
    parser.add_argument(
        "--render-only",
        action="store_true",
        help="Re-render summary.md from results.json/metrics.json in --out (no API calls).",
    )
    parser.add_argument(
        "--strict", action="store_true", help="Exit with code 1 when a target is not met."
    )
    return parser.parse_args(argv)


def _comparison_inputs(
    args: argparse.Namespace, out_dir: Path
) -> tuple[dict | None, list | None, str | None, str | None]:
    comparison_path = args.comparison.resolve() if args.comparison else None
    comparison = None
    if comparison_path and comparison_path.parent != out_dir:
        comparison = load_comparison(comparison_path)
    tuning = load_tuning(args.tuning) if args.tuning else None
    return (
        comparison,
        tuning,
        _read_note(args.notes_dir, "tuning.md"),
        _read_note(args.notes_dir, "review.md"),
    )


def render_only(args: argparse.Namespace) -> int:
    out_dir = args.out.resolve()
    try:
        results, info = load_run(out_dir)
    except FileNotFoundError as exc:
        print(f"Error: {exc}. Run the evaluation first.", file=sys.stderr)
        return 2
    comparison, tuning, tuning_notes, review_notes = _comparison_inputs(args, out_dir)
    path = out_dir / "summary.md"
    write_summary(
        path,
        results,
        aggregate(results),
        info,
        comparison=comparison,
        tuning=tuning,
        tuning_notes=tuning_notes,
        review_notes=review_notes,
    )
    print(f"wrote {path}")
    return 0


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    configure_logging("INFO" if args.verbose else "WARNING")
    base = get_settings()
    defaults = EvalConfig.from_settings(base)
    config = EvalConfig(
        top_k=args.top_k if args.top_k is not None else defaults.top_k,
        threshold=args.threshold if args.threshold is not None else defaults.threshold,
        chunk_size=args.chunk_size if args.chunk_size is not None else defaults.chunk_size,
        chunk_overlap=(
            args.chunk_overlap if args.chunk_overlap is not None else defaults.chunk_overlap
        ),
    )
    if args.render_only:
        return render_only(args)

    pricing = pricing_from_args(args)
    questions = load_questions(args.questions)

    try:
        settings = settings_for(base, config)
        settings.require_openai_api_key()
        store = prepare_vectorstore(settings, base)
    except (IndexNotReadyError, MissingOpenAIKeyError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    print(f"Evaluating {len(questions)} questions ({config.label}) ...", flush=True)
    results = run_questions(questions, settings, store, pricing=pricing)
    if not args.no_ragas:
        from eval.ragas_scoring import score_results

        print("Scoring with RAGAS ...", flush=True)
        score_results(results, settings, judge_model=args.judge_model, concurrency=args.concurrency)
        rediagnose(results, settings.retrieval_score_threshold)

    metrics = aggregate(results)
    targets = Targets()
    info = RunInfo(
        generated_at=datetime.now().astimezone().isoformat(timespec="seconds"),
        config={
            "chunk_size": config.chunk_size,
            "chunk_overlap": config.chunk_overlap,
            "top_k": config.top_k,
            "threshold": config.threshold,
            "collection": settings.chroma_collection,
            "max_context_tokens": settings.rag_max_context_tokens,
        },
        chat_model=settings.openai_chat_model,
        embedding_model=settings.openai_embedding_model,
        judge_model=None if args.no_ragas else (args.judge_model or settings.openai_chat_model),
        pricing=pricing,
        targets=targets,
        ragas=not args.no_ragas,
        label=args.label,
    )

    out_dir = args.out.resolve()
    comparison, tuning, tuning_notes, review_notes = _comparison_inputs(args, out_dir)
    paths = write_reports(
        out_dir,
        results,
        metrics,
        info,
        comparison=comparison,
        tuning=tuning,
        tuning_notes=tuning_notes,
        review_notes=review_notes,
    )

    checks = target_checks(metrics, targets)
    print()
    for name, value, target, met in checks:
        status = {True: "met", False: "NOT MET", None: "n/a"}[met]
        print(
            f"  {METRIC_LABELS[name]:<30} {fmt_metric(name, value):>8}  target {target:<7} {status}"
        )
    for name in (
        "key_fact_accuracy",
        "answer_relevancy",
        "context_precision",
        "context_recall",
        "avg_latency_ms",
        "avg_cost_usd",
    ):
        print(f"  {METRIC_LABELS[name]:<30} {fmt_metric(name, metrics.get(name)):>8}")
    print(f"\n  Passed {metrics['passed']}/{metrics['questions']} questions")
    for path in paths.values():
        print(f"  wrote {path}")

    if metrics["errors"]:
        return 1
    if args.strict and any(met is False for *_, met in checks):
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
