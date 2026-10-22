"""Scored retrieval with a similarity threshold.

`retrieve(question, k)` returns the top-k chunks as `RetrievedChunk` objects whose `score`
is a cosine similarity clamped to 0-1 (higher is more relevant). Chroma returns cosine
*distance* (``1 - cosine_similarity``, 0-2); `distance_to_similarity()` is the single place
where that conversion happens. `filter_by_threshold()` drops chunks below
RETRIEVAL_SCORE_THRESHOLD.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass
from typing import Any

from langchain_chroma import Chroma
from langchain_core.documents import Document

from app.config import Settings, get_settings
from app.ingestion.chunker import CHUNK_METADATA_KEYS
from app.retrieval.vectorstore import ensure_cosine, get_vectorstore

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class RetrievedChunk:
    """A retrieved chunk with its 0-1 similarity score (higher is more relevant)."""

    doc: Document
    score: float

    @property
    def metadata(self) -> dict[str, Any]:
        return self.doc.metadata

    @property
    def chunk_id(self) -> str:
        return str(self.doc.metadata["chunk_id"])

    @property
    def text(self) -> str:
        return self.doc.page_content


def distance_to_similarity(distance: float) -> float:
    """Convert a Chroma cosine distance (0-2, lower is closer) to a 0-1 similarity.

    cosine_similarity = 1 - distance; negative similarities (unrelated or opposite
    vectors) are clamped to 0 so that every score lies in [0, 1].
    """
    return min(1.0, max(0.0, 1.0 - float(distance)))


def _normalize_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    """Restore contract keys Chroma dropped because their value was None (e.g. section)."""
    normalized = dict(metadata)
    for key in CHUNK_METADATA_KEYS:
        normalized.setdefault(key, None)
    return normalized


def retrieve(
    question: str,
    k: int | None = None,
    *,
    vectorstore: Chroma | None = None,
    settings: Settings | None = None,
) -> list[RetrievedChunk]:
    """Return the `k` most similar chunks for `question`, best first.

    `k` defaults to RETRIEVAL_TOP_K. No threshold is applied here; use
    `filter_by_threshold()` on the result.
    """
    s = settings or get_settings()
    query = question.strip()
    if not query:
        raise ValueError("question must not be empty")
    top_k = s.retrieval_top_k if k is None else k
    if top_k <= 0:
        raise ValueError(f"k must be positive (got {top_k})")

    store = vectorstore if vectorstore is not None else get_vectorstore(s)
    ensure_cosine(store)
    pairs = store.similarity_search_with_score(query, k=top_k)

    results = [
        RetrievedChunk(
            doc=Document(page_content=doc.page_content, metadata=_normalize_metadata(doc.metadata)),
            score=distance_to_similarity(distance),
        )
        for doc, distance in pairs
    ]
    results.sort(key=lambda chunk: chunk.score, reverse=True)
    logger.debug(
        "retrieved chunks",
        extra={
            "k": top_k,
            "returned": len(results),
            "top_score": round(results[0].score, 4) if results else None,
        },
    )
    return results


def filter_by_threshold(
    chunks: Iterable[RetrievedChunk], threshold: float | None = None
) -> list[RetrievedChunk]:
    """Keep chunks whose score is at least `threshold` (default RETRIEVAL_SCORE_THRESHOLD)."""
    limit = get_settings().retrieval_score_threshold if threshold is None else threshold
    return [chunk for chunk in chunks if chunk.score >= limit]
