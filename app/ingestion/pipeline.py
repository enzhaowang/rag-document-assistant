"""Ingestion pipeline and CLI entry point: `python -m app.ingestion.pipeline`.

`load_and_chunk(pdf_dir)` turns every PDF under `pdf_dir` into chunk Documents with the
shared metadata contract. The CLI prints statistics about the run:

    python -m app.ingestion.pipeline --dry-run              # parse + chunk, print stats
    python -m app.ingestion.pipeline --dry-run --sample 3   # also print 3 example chunks
    python -m app.ingestion.pipeline --dry-run --dump chunks.jsonl

TODO(P3): `ingest()` that upserts chunks into the vector store idempotently.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import statistics
import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path

from langchain_core.documents import Document

from app.config import Settings, get_settings
from app.ingestion.chunker import chunk_documents, count_tokens, slugify
from app.ingestion.loader import PdfLoadError, find_pdfs, load_pdf
from app.logging_config import configure_logging

logger = logging.getLogger(__name__)


@dataclass
class SkippedFile:
    source: str
    reason: str


@dataclass
class IngestionResult:
    """Chunks produced from a PDF directory plus run statistics."""

    chunks: list[Document] = field(default_factory=list)
    files: int = 0
    pages: int = 0
    skipped: list[SkippedFile] = field(default_factory=list)

    @property
    def token_counts(self) -> list[int]:
        return [count_tokens(chunk.page_content) for chunk in self.chunks]

    def stats(self) -> dict[str, object]:
        tokens = self.token_counts
        return {
            "files": self.files,
            "files_skipped": len(self.skipped),
            "pages": self.pages,
            "chunks": len(self.chunks),
            "avg_tokens": round(statistics.fmean(tokens), 1) if tokens else 0.0,
            "min_tokens": min(tokens, default=0),
            "max_tokens": max(tokens, default=0),
        }


def _unique_slugs(paths: Sequence[Path]) -> dict[Path, str]:
    """Map each file to a slug; colliding slugs get a short hash of the file name appended."""
    slugs = {path: slugify(path.name) for path in paths}
    seen: dict[str, int] = {}
    for slug in slugs.values():
        seen[slug] = seen.get(slug, 0) + 1
    for path, slug in slugs.items():
        if seen[slug] > 1:
            name_hash = hashlib.sha256(path.name.encode("utf-8")).hexdigest()
            slugs[path] = f"{slug}-{name_hash[:8]}"
    return slugs


def run(pdf_dir: Path, settings: Settings | None = None) -> IngestionResult:
    """Load and chunk every PDF under `pdf_dir`, skipping files that cannot be read."""
    s = settings or get_settings()
    if not pdf_dir.is_dir():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    paths = find_pdfs(pdf_dir)
    if not paths:
        logger.warning("no PDF files found", extra={"pdf_dir": str(pdf_dir)})
    slugs = _unique_slugs(paths)

    result = IngestionResult()
    for path in paths:
        try:
            pages = load_pdf(path, root=pdf_dir)
        except PdfLoadError as exc:
            logger.warning(
                "skipping unreadable PDF", extra={"source": path.name, "reason": str(exc)}
            )
            result.skipped.append(SkippedFile(source=path.name, reason=str(exc)))
            continue
        chunks = chunk_documents(pages, slugs[path], s)
        result.files += 1
        result.pages += len(pages)
        result.chunks.extend(chunks)
        logger.info(
            "chunked pdf",
            extra={"source": path.name, "pages": len(pages), "chunks": len(chunks)},
        )
    return result


def load_and_chunk(pdf_dir: Path | str, settings: Settings | None = None) -> list[Document]:
    """Return chunk Documents for every readable PDF under `pdf_dir`."""
    return run(Path(pdf_dir), settings).chunks


def _print_stats(result: IngestionResult, pdf_dir: Path) -> None:
    stats = result.stats()
    print(f"PDF directory : {pdf_dir}")
    print(f"Files         : {stats['files']} processed, {stats['files_skipped']} skipped")
    for skipped in result.skipped:
        print(f"  - skipped {skipped.source}: {skipped.reason}")
    print(f"Pages         : {stats['pages']} (non-blank)")
    print(f"Chunks        : {stats['chunks']}")
    print(
        f"Tokens/chunk  : avg {stats['avg_tokens']}, "
        f"min {stats['min_tokens']}, max {stats['max_tokens']}"
    )


def _print_samples(chunks: Sequence[Document], count: int) -> None:
    if count <= 0 or not chunks:
        return
    step = max(len(chunks) // count, 1)
    for chunk in list(chunks)[::step][:count]:
        meta = chunk.metadata
        print()
        print(f"--- {meta['chunk_id']} | {meta['source']} p.{meta['page']} | {meta['section']}")
        print(chunk.page_content)


def _dump(chunks: Sequence[Document], path: Path) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for chunk in chunks:
            record = {"text": chunk.page_content, "metadata": chunk.metadata}
            handle.write(json.dumps(record, ensure_ascii=False) + "\n")
    print(f"Wrote {len(chunks)} chunks to {path}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        prog="python -m app.ingestion.pipeline",
        description="Parse and chunk the PDF knowledge base.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk only, print statistics; do not write to the vector store.",
    )
    parser.add_argument(
        "--pdf-dir", type=Path, default=None, help="PDF directory (default: PDF_DIR setting)."
    )
    parser.add_argument(
        "--sample", type=int, default=0, metavar="N", help="Print N example chunks."
    )
    parser.add_argument(
        "--dump", type=Path, default=None, metavar="PATH", help="Write all chunks as JSON lines."
    )
    args = parser.parse_args(argv)

    configure_logging()
    settings = get_settings()
    pdf_dir = args.pdf_dir or settings.pdf_dir

    if not args.dry_run:
        print(
            "Vector store indexing is not available yet; "
            "run with --dry-run to parse and chunk only.",
            file=sys.stderr,
        )
        return 2

    try:
        result = run(pdf_dir, settings)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    _print_stats(result, pdf_dir)
    _print_samples(result.chunks, args.sample)
    if args.dump:
        _dump(result.chunks, args.dump)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
