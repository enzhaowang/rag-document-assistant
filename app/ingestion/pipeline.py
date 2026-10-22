"""Ingestion pipeline and CLI entry point: `python -m app.ingestion.pipeline`.

`load_and_chunk(pdf_dir)` turns every PDF under `pdf_dir` into chunk Documents with the
shared metadata contract. `ingest(pdf_dir)` additionally syncs those chunks into the vector
store (see `ingest()` for the idempotency rules). The CLI prints statistics about the run:

    python -m app.ingestion.pipeline                        # index new/changed PDFs
    python -m app.ingestion.pipeline --reset                # drop the collection, re-index all
    python -m app.ingestion.pipeline --dry-run              # parse + chunk only, print stats
    python -m app.ingestion.pipeline --dry-run --sample 3   # also print 3 example chunks
    python -m app.ingestion.pipeline --dry-run --dump chunks.jsonl
"""

from __future__ import annotations

import argparse
import hashlib
import json
import logging
import statistics
import sys
import time
from collections.abc import Callable, Iterable, Sequence
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, TypeVar

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import MissingOpenAIKeyError, Settings, get_settings
from app.ingestion.chunker import chunk_documents, count_tokens, slugify
from app.ingestion.loader import PdfLoadError, find_pdfs, load_pdf
from app.logging_config import configure_logging
from app.retrieval.vectorstore import VectorStoreConfigError, ensure_cosine, get_vectorstore

logger = logging.getLogger(__name__)

T = TypeVar("T")


@dataclass
class SkippedFile:
    source: str
    reason: str
    # chunk_id prefix the file would use; lets `ingest()` keep its previously indexed chunks.
    doc_slug: str | None = None


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


def _relative_name(path: Path, root: Path) -> str:
    """Return `path` relative to `root` in POSIX form (the file name if outside `root`)."""
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.name


def _unique_slugs(paths: Sequence[Path], root: Path) -> dict[Path, str]:
    """Map each file to a slug derived from its file name.

    Slugs that collide (e.g. `a/FAQ.pdf` and `b/FAQ.pdf`, or `FAQ.pdf` and `faq.pdf`) get a
    short hash of the path relative to `root` appended, so every file keeps a distinct and
    deterministic chunk_id prefix. Non-colliding slugs are left unchanged.
    """
    slugs = {path: slugify(path.name) for path in paths}
    seen: dict[str, int] = {}
    for slug in slugs.values():
        seen[slug] = seen.get(slug, 0) + 1
    for path, slug in slugs.items():
        if seen[slug] > 1:
            rel_hash = hashlib.sha256(_relative_name(path, root).encode("utf-8")).hexdigest()
            slugs[path] = f"{slug}-{rel_hash[:8]}"
    return slugs


def run(pdf_dir: Path, settings: Settings | None = None) -> IngestionResult:
    """Load and chunk every PDF under `pdf_dir`, skipping files that cannot be read.

    Note: chunk metadata `source` is the bare file name, so files with the same name in
    different subdirectories share a `source` value; their chunk_ids remain distinct.
    """
    s = settings or get_settings()
    if not pdf_dir.is_dir():
        raise FileNotFoundError(f"PDF directory not found: {pdf_dir}")

    paths = find_pdfs(pdf_dir)
    if not paths:
        logger.warning("no PDF files found", extra={"pdf_dir": str(pdf_dir)})
    slugs = _unique_slugs(paths, pdf_dir)

    result = IngestionResult()
    for path in paths:
        try:
            pages = load_pdf(path, root=pdf_dir)
        except (PdfLoadError, OSError) as exc:
            source = _relative_name(path, pdf_dir)
            logger.warning("skipping unreadable PDF", extra={"source": source, "reason": str(exc)})
            result.skipped.append(SkippedFile(source=source, reason=str(exc), doc_slug=slugs[path]))
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


# --------------------------------------------------------------------------- indexing

# Chunks embedded and upserted per vector store call.
DEFAULT_BATCH_SIZE = 100
# Attempts per batch (first try + retries) and the base delay of the exponential backoff.
MAX_ATTEMPTS = 5
BACKOFF_BASE_SECONDS = 1.0
# HTTP status codes that will not succeed on retry (bad request, auth, not found, ...).
NON_RETRYABLE_STATUS = frozenset({400, 401, 403, 404, 409, 422})
# Page size when reading existing records back from the vector store.
_READ_PAGE_SIZE = 1000


@dataclass
class IndexStats:
    """What `ingest()` changed in the vector store."""

    files_new: int = 0
    files_changed: int = 0
    files_unchanged: int = 0
    files_removed: int = 0
    chunks_added: int = 0
    chunks_deleted: int = 0
    chunks_total: int = 0
    reset: bool = False


@dataclass
class _IndexedDoc:
    ids: set[str] = field(default_factory=set)
    hashes: set[str] = field(default_factory=set)


def doc_slug_of(chunk_id: str) -> str:
    """Return the document slug prefix of a chunk_id ("{doc_slug}__p{page}__c{idx}")."""
    return chunk_id.split("__", 1)[0]


def _chroma_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Drop None values: Chroma cannot store them (the retriever restores missing keys)."""
    return {key: value for key, value in metadata.items() if value is not None}


def _is_retryable(exc: Exception) -> bool:
    if isinstance(exc, MissingOpenAIKeyError | VectorStoreConfigError):
        return False
    status = getattr(exc, "status_code", None)
    return status not in NON_RETRYABLE_STATUS


def call_with_retry(
    fn: Callable[[], T],
    *,
    what: str,
    attempts: int = MAX_ATTEMPTS,
    base_delay: float = BACKOFF_BASE_SECONDS,
    sleep: Callable[[float], None] = time.sleep,
) -> T:
    """Call `fn`, retrying transient failures with exponential backoff (1s, 2s, 4s, ...)."""
    for attempt in range(1, attempts + 1):
        try:
            return fn()
        except Exception as exc:
            if attempt >= attempts or not _is_retryable(exc):
                raise
            delay = base_delay * 2 ** (attempt - 1)
            logger.warning(
                "vector store call failed, retrying",
                extra={
                    "what": what,
                    "attempt": attempt,
                    "retry_in_s": delay,
                    "error": f"{type(exc).__name__}: {exc}",
                },
            )
            sleep(delay)
    raise AssertionError("unreachable")  # pragma: no cover


def _indexed_docs(store: Chroma) -> dict[str, _IndexedDoc]:
    """Read every record's id and doc_hash from the store, grouped by document slug."""
    docs: dict[str, _IndexedDoc] = {}
    offset = 0
    while True:
        page = store.get(include=["metadatas"], limit=_READ_PAGE_SIZE, offset=offset)
        ids: list[str] = page["ids"]
        for chunk_id, metadata in zip(ids, page["metadatas"], strict=True):
            entry = docs.setdefault(doc_slug_of(chunk_id), _IndexedDoc())
            entry.ids.add(chunk_id)
            entry.hashes.add(str((metadata or {}).get("doc_hash")))
        if len(ids) < _READ_PAGE_SIZE:
            return docs
        offset += len(ids)


def _upsert(
    store: Chroma, chunks: Sequence[Document], batch_size: int, sleep: Callable[[float], None]
) -> int:
    """Embed and upsert `chunks` in batches, keyed by chunk_id. Returns the number written."""
    written = 0
    for start in range(0, len(chunks), batch_size):
        batch = list(chunks[start : start + batch_size])
        documents = [
            Document(page_content=c.page_content, metadata=_chroma_metadata(c.metadata))
            for c in batch
        ]
        ids = [c.metadata["chunk_id"] for c in batch]
        call_with_retry(
            lambda documents=documents, ids=ids: store.add_documents(documents, ids=ids),
            what=f"upsert {len(ids)} chunks",
            sleep=sleep,
        )
        written += len(ids)
        logger.info("upserted batch", extra={"chunks": len(ids), "written": written})
    return written


def _delete(
    store: Chroma, ids: Iterable[str], batch_size: int, sleep: Callable[[float], None]
) -> int:
    ordered = sorted(ids)
    for start in range(0, len(ordered), batch_size):
        batch = ordered[start : start + batch_size]
        call_with_retry(
            lambda batch=batch: store.delete(ids=batch),
            what=f"delete {len(batch)} chunks",
            sleep=sleep,
        )
    return len(ordered)


def ingest(
    pdf_dir: Path | str | None = None,
    settings: Settings | None = None,
    *,
    vectorstore: Chroma | None = None,
    reset: bool = False,
    batch_size: int = DEFAULT_BATCH_SIZE,
    sleep: Callable[[float], None] = time.sleep,
) -> tuple[IngestionResult, IndexStats]:
    """Sync the chunks of every PDF under `pdf_dir` into the vector store.

    Idempotent: chunk_id is the vector ID, so writes are upserts. Per document (keyed by
    the chunk_id slug prefix):

    - unchanged (same doc_hash and same chunk_ids already stored): skipped, no embedding;
    - new or changed: chunk_ids that no longer exist are deleted, then all chunks are
      re-embedded and upserted;
    - removed from `pdf_dir`: all its chunks are deleted;
    - unreadable this run (skipped by the loader): its existing chunks are kept.

    `reset=True` drops and re-creates the collection first. Embedding/upsert calls run in
    batches of `batch_size` with exponential-backoff retries.
    """
    s = settings or get_settings()
    if batch_size <= 0:
        raise ValueError(f"batch_size must be positive (got {batch_size})")
    directory = Path(pdf_dir) if pdf_dir is not None else s.pdf_dir
    result = run(directory, s)

    store = vectorstore if vectorstore is not None else get_vectorstore(s)
    stats = IndexStats(reset=reset)
    if reset:
        store.reset_collection()
        ensure_cosine(store)
        logger.info("vector store collection reset", extra={"collection": s.chroma_collection})

    existing = _indexed_docs(store)
    current: dict[str, list[Document]] = {}
    for chunk in result.chunks:
        current.setdefault(doc_slug_of(chunk.metadata["chunk_id"]), []).append(chunk)

    for slug, chunks in current.items():
        new_ids = {c.metadata["chunk_id"] for c in chunks}
        new_hash = chunks[0].metadata["doc_hash"]
        old = existing.get(slug)
        source = chunks[0].metadata["source"]
        if old is not None and old.hashes == {new_hash} and old.ids == new_ids:
            stats.files_unchanged += 1
            logger.info("document unchanged, skipped", extra={"source": source})
            continue
        if old is None:
            stats.files_new += 1
        else:
            stats.files_changed += 1
            stats.chunks_deleted += _delete(store, old.ids - new_ids, batch_size, sleep)
        stats.chunks_added += _upsert(store, chunks, batch_size, sleep)
        logger.info(
            "document indexed",
            extra={"source": source, "chunks": len(chunks), "changed": old is not None},
        )

    keep = set(current) | {f.doc_slug for f in result.skipped if f.doc_slug}
    for slug, old in existing.items():
        if slug in keep:
            continue
        stats.files_removed += 1
        stats.chunks_deleted += _delete(store, old.ids, batch_size, sleep)
        logger.info("document removed from index", extra={"doc_slug": slug})

    stats.chunks_total = store._collection.count()
    logger.info("ingest finished", extra=asdict(stats))
    return result, stats


def _print_index_stats(stats: IndexStats, settings: Settings) -> None:
    target = (
        f"{settings.chroma_persist_dir} (local)"
        if settings.chroma_mode == "local"
        else f"{settings.chroma_host}:{settings.chroma_port} (http)"
    )
    print(f"Vector store  : collection {settings.chroma_collection!r} at {target}")
    if stats.reset:
        print("Reset         : collection dropped and re-created")
    print(
        f"Documents     : {stats.files_new} new, {stats.files_changed} changed, "
        f"{stats.files_unchanged} unchanged, {stats.files_removed} removed"
    )
    print(f"New chunks    : {stats.chunks_added} (embedded and upserted)")
    print(f"Deleted chunks: {stats.chunks_deleted}")
    print(f"Total chunks  : {stats.chunks_total} in collection")


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
        description="Parse, chunk and index the PDF knowledge base into the vector store.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Parse and chunk only, print statistics; do not write to the vector store.",
    )
    parser.add_argument(
        "--reset",
        action="store_true",
        help="Drop and re-create the vector store collection, then index every PDF.",
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

    if args.dry_run and args.reset:
        parser.error("--reset cannot be combined with --dry-run")

    try:
        if args.dry_run:
            result = run(pdf_dir, settings)
            index_stats = None
        else:
            result, index_stats = ingest(pdf_dir, settings, reset=args.reset)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    except (MissingOpenAIKeyError, VectorStoreConfigError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    _print_stats(result, pdf_dir)
    if index_stats is not None:
        _print_index_stats(index_stats, settings)
    _print_samples(result.chunks, args.sample)
    if args.dump:
        _dump(result.chunks, args.dump)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
