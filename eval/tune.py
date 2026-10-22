"""Sweep retrieval and chunking parameters on the evaluation questions.

For every combination of chunk size, top-k and score threshold, all questions are answered
with `answer_question()` and the custom metrics (citation hit rate, refusal rates,
retrieval hit rate, latency, cost) are recorded. RAGAS is not run here, to keep sweeps
fast and cheap; run `make eval` on the chosen settings for the full picture.

Chunk sizes other than CHUNK_SIZE_TOKENS are indexed into separate eval collections
(`<CHROMA_COLLECTION>_eval_cs<size>_ov<overlap>`); the main index is not modified.

Answers vary slightly between runs even at temperature 0, so `--repeats N` runs each
configuration N times: metrics are averaged and failed questions are listed with how
often they failed (for example "SF-01 (1/3)").

Writes eval/reports/tuning.csv, which `make eval` includes in summary.md.

Usage:
    python -m eval.tune
    python -m eval.tune --thresholds 0.3,0.4 --top-ks 4,6 --chunk-sizes 300:50,500:80
    python -m eval.tune --chunk-sizes 500:80 --top-ks 6 --thresholds 0.35,0.4 --repeats 3 --append

Requires an indexed vector store (`make ingest`) and makes real API calls.
"""

from __future__ import annotations

import argparse
import statistics
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from pathlib import Path

import pandas as pd

from app.config import get_settings
from app.logging_config import configure_logging
from eval.dataset import load_questions
from eval.metrics import aggregate
from eval.run_eval import DEFAULT_TUNING, add_config_arguments, pricing_from_args
from eval.runner import (
    EvalConfig,
    IndexNotReadyError,
    prepare_vectorstore,
    run_questions,
    settings_for,
)

TUNING_COLUMNS = (
    "chunk_size",
    "chunk_overlap",
    "top_k",
    "threshold",
    "runs",
    "passed",
    "citation_hit_rate",
    "key_fact_accuracy",
    "out_of_scope_refusal_rate",
    "false_refusal_rate",
    "retrieval_hit_rate",
    "avg_latency_ms",
    "avg_cost_usd",
    "errors",
    "failed_questions",
)


def _floats(text: str) -> list[float]:
    return [float(v) for v in text.split(",") if v.strip()]


def _ints(text: str) -> list[int]:
    return [int(v) for v in text.split(",") if v.strip()]


def _chunkings(text: str) -> list[tuple[int, int]]:
    pairs = []
    for item in text.split(","):
        if not item.strip():
            continue
        size, _, overlap = item.partition(":")
        if not overlap:
            raise argparse.ArgumentTypeError(f"expected SIZE:OVERLAP, got {item!r}")
        pairs.append((int(size), int(overlap)))
    return pairs


def summarize_runs(
    run_metrics: Sequence[Mapping[str, float | int | None]],
    run_failures: Sequence[Sequence[str]],
) -> dict[str, object]:
    """Average the metrics of repeated runs and count how often each question failed."""
    summary: dict[str, object] = {"runs": len(run_metrics)}
    for name in TUNING_COLUMNS:
        values = [m[name] for m in run_metrics if m.get(name) is not None]
        if values:
            summary[name] = statistics.fmean(values)
    counts = Counter(qid for failures in run_failures for qid in failures)
    order = list(dict.fromkeys(qid for failures in run_failures for qid in failures))
    if len(run_metrics) == 1:
        summary["failed_questions"] = " ".join(order)
    else:
        summary["failed_questions"] = ", ".join(
            f"{qid} ({counts[qid]}/{len(run_metrics)})" for qid in order
        )
    return summary


def build_grid(
    chunkings: Sequence[tuple[int, int]], top_ks: Sequence[int], thresholds: Sequence[float]
) -> list[EvalConfig]:
    """Full grid, ordered by chunking, then top-k, then threshold."""
    return [
        EvalConfig(top_k=k, threshold=t, chunk_size=size, chunk_overlap=overlap)
        for size, overlap in chunkings
        for k in top_ks
        for t in thresholds
    ]


CONFIG_KEYS = ["chunk_size", "chunk_overlap", "top_k", "threshold"]


def merge_runs(existing: pd.DataFrame, new: pd.DataFrame) -> pd.DataFrame:
    """Combine two sweeps; `new` wins for identical configurations. Sorted by config."""
    combined = pd.concat([existing, new], ignore_index=True)
    if "runs" in combined:
        combined["runs"] = combined["runs"].fillna(1).astype(int)
    combined = combined.drop_duplicates(subset=CONFIG_KEYS, keep="last")
    return (
        combined.sort_values(CONFIG_KEYS)
        .reset_index(drop=True)
        .reindex(columns=list(TUNING_COLUMNS))
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    add_config_arguments(parser)
    parser.add_argument(
        "--chunk-sizes", type=_chunkings, default=_chunkings("300:50,500:80,800:120"),
        help="Comma-separated SIZE:OVERLAP pairs (default 300:50,500:80,800:120).",
    )  # fmt: skip
    parser.add_argument(
        "--top-ks", type=_ints, default=_ints("3,4,6,8"),
        help="Comma-separated top-k values (default 3,4,6,8).",
    )  # fmt: skip
    parser.add_argument(
        "--thresholds", type=_floats, default=_floats("0.3,0.4,0.5"),
        help="Comma-separated score thresholds (default 0.3,0.4,0.5).",
    )  # fmt: skip
    parser.add_argument("--workers", type=int, default=4, help="Parallel questions per config.")
    parser.add_argument("--repeats", type=int, default=1, help="Runs per configuration.")
    parser.add_argument("--out", type=Path, default=DEFAULT_TUNING, help="Output CSV path.")
    parser.add_argument(
        "--append",
        action="store_true",
        help="Merge into an existing --out file (rows of re-run configurations are replaced).",
    )
    args = parser.parse_args(argv)

    configure_logging("INFO" if args.verbose else "WARNING")
    base = get_settings()
    pricing = pricing_from_args(args)
    questions = load_questions(args.questions)
    grid = build_grid(args.chunk_sizes, args.top_ks, args.thresholds)

    rows = []
    stores: dict[tuple[int, int], object] = {}
    for i, config in enumerate(grid, start=1):
        settings = settings_for(base, config)
        key = (config.chunk_size, config.chunk_overlap)
        try:
            if key not in stores:
                stores[key] = prepare_vectorstore(settings, base)
        except IndexNotReadyError as exc:
            print(f"Error: {exc}", file=sys.stderr)
            return 2
        run_metrics = []
        run_failures = []
        for _ in range(max(1, args.repeats)):
            results = run_questions(
                questions, settings, stores[key], pricing=pricing, workers=args.workers
            )
            run_metrics.append(aggregate(results))
            run_failures.append([r.id for r in results if not r.passed])
        summary = summarize_runs(run_metrics, run_failures)
        rows.append(
            {
                "chunk_size": config.chunk_size,
                "chunk_overlap": config.chunk_overlap,
                "top_k": config.top_k,
                "threshold": config.threshold,
                **summary,
            }
        )
        print(
            f"[{i:>2}/{len(grid)}] {config.label}: passed {summary['passed']:.1f}/"
            f"{len(questions)}, citation hit {summary['citation_hit_rate']:.0%}, "
            f"OOS refused {summary['out_of_scope_refusal_rate']:.0%}, "
            f"false refusals {summary['false_refusal_rate']:.0%}, "
            f"avg cost ${summary.get('avg_cost_usd') or 0:.5f}"
            + (f"  failed: {summary['failed_questions']}" if summary["failed_questions"] else ""),
            flush=True,
        )

    frame = pd.DataFrame(rows, columns=list(TUNING_COLUMNS))
    if args.append and args.out.is_file():
        frame = merge_runs(pd.read_csv(args.out), frame)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_csv(args.out, index=False)
    print(f"\nwrote {args.out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
