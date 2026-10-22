"""Measure retrieval quality against facts listed in data/pdfs/FACTS.md.

Asks 10 natural-language questions, each tied to a fact ID in FACTS.md, and checks whether
a chunk from the fact's file and page(s) appears in the top-k results. Expected files and
pages are read from FACTS.md, so they always match the generated PDFs. The mix covers
plain text, table rows, a cross-page statement and confusable T2/T3 facts.

Requires an indexed vector store (`make ingest`) and makes real embedding API calls.

Usage: python scripts/check_retrieval.py [--k 6] [--min-hit-rate 0.8]
Exit code is 0 when the hit rate reaches --min-hit-rate, otherwise 1.
"""

from __future__ import annotations

import argparse
import re
import statistics
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.config import get_settings  # noqa: E402
from app.retrieval.retriever import retrieve  # noqa: E402
from app.retrieval.vectorstore import get_vectorstore  # noqa: E402

# (fact ID in FACTS.md, question a support agent might ask)
QUESTIONS: tuple[tuple[str, str], ...] = (
    ("PG-T2-04", "What does error code E4 mean on the Thermostat T2?"),
    ("PG-T3-04", "Which error does the T3 thermostat show when it loses Wi-Fi?"),
    ("PG-T3-06", "How long is the warranty on the Lumora Thermostat T3?"),
    ("PG-T3-05", "When is a C-wire mandatory for the T3 thermostat?"),
    ("SOP-RET-04", "Who has to approve a refund of $800 on one order?"),
    ("SOP-RET-03", "When is a restocking fee charged on an opened return?"),
    ("SOP-ESC-06", "What is the goodwill credit limit for a Tier 2 agent?"),
    ("SOP-RMA-01", "What format do RMA numbers use and how long is an RMA valid?"),
    ("FAQ-SHP-01", "How much does standard shipping cost and when is it free?"),
    ("FAQ-APP-01", "How many failed sign-in attempts lock an account, and for how long?"),
)

_PAGES = re.compile(r"^(\d+)(?:-(\d+))?$")


@dataclass(frozen=True)
class Fact:
    fact_id: str
    text: str
    source: str
    pages: frozenset[int]


def parse_facts(path: Path) -> dict[str, Fact]:
    """Parse the facts table of FACTS.md (ID | Fact | File | Page(s) | Kind | Tags)."""
    facts: dict[str, Fact] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 4:
            continue
        match = _PAGES.match(cells[3])
        if not match:
            continue
        first = int(match.group(1))
        last = int(match.group(2) or first)
        facts[cells[0]] = Fact(cells[0], cells[1], cells[2], frozenset(range(first, last + 1)))
    return facts


def main(argv: Sequence[str] | None = None) -> int:
    settings = get_settings()
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--k", type=int, default=settings.retrieval_top_k, help="Top-k to check.")
    parser.add_argument("--min-hit-rate", type=float, default=0.8, help="Pass threshold (0-1).")
    parser.add_argument(
        "--facts", type=Path, default=settings.pdf_dir / "FACTS.md", help="Path to FACTS.md."
    )
    args = parser.parse_args(argv)

    facts = parse_facts(args.facts)
    missing = [fact_id for fact_id, _ in QUESTIONS if fact_id not in facts]
    if missing:
        print(f"Fact IDs not found in {args.facts}: {', '.join(missing)}", file=sys.stderr)
        return 1

    store = get_vectorstore(settings)
    if store._collection.count() == 0:
        print("The vector store is empty; run `make ingest` first.", file=sys.stderr)
        return 1

    hits = 0
    top_scores: list[float] = []
    print(f"Top-{args.k} retrieval check on {len(QUESTIONS)} facts from {args.facts}\n")
    for fact_id, question in QUESTIONS:
        fact = facts[fact_id]
        results = retrieve(question, k=args.k, vectorstore=store, settings=settings)
        rank = next(
            (
                i
                for i, chunk in enumerate(results, start=1)
                if chunk.metadata["source"] == fact.source and chunk.metadata["page"] in fact.pages
            ),
            None,
        )
        hits += rank is not None
        if results:
            top_scores.append(results[0].score)
        pages = ",".join(str(p) for p in sorted(fact.pages))
        status = f"HIT  rank {rank}" if rank else "MISS"
        print(f"[{status:<10}] {fact_id:<11} {question}")
        print(f"             expected: {fact.source} p.{pages}")
        for i, chunk in enumerate(results[:3], start=1):
            meta = chunk.metadata
            print(f"             #{i} {chunk.score:.3f}  {meta['source']} p.{meta['page']}")

    rate = hits / len(QUESTIONS)
    print()
    print(
        f"Hit rate      : {hits}/{len(QUESTIONS)} = {rate:.0%} (required {args.min_hit_rate:.0%})"
    )
    if top_scores:
        print(
            f"Top-1 scores  : min {min(top_scores):.3f}, "
            f"mean {statistics.fmean(top_scores):.3f}, max {max(top_scores):.3f}"
        )
    return 0 if rate >= args.min_hit_rate else 1


if __name__ == "__main__":
    raise SystemExit(main())
