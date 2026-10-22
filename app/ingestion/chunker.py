"""Split page documents into token-sized chunks with citation metadata.

Every page is split on its own, so each chunk belongs to exactly one page and its page
number is always exact. Chunks carry the metadata contract shared by all later stages:

    chunk_id     "{doc_slug}__p{page}__c{chunk_index}" (deterministic)
    source       original file name, e.g. "SOP - Returns and Refunds.pdf"
    doc_title    PDF metadata title, or the file name without extension
    doc_type     product_guide | sop | faq | policy | other
    page         1-based page number, as shown in a PDF reader
    chunk_index  0-based position of the chunk within its page
    doc_hash     SHA-256 of the source file
    section      nearest preceding section heading, or None
"""

from __future__ import annotations

import logging
import re
from collections.abc import Iterable, Sequence
from functools import lru_cache
from pathlib import Path

import tiktoken
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from app.config import Settings, get_settings
from app.ingestion.loader import Heading

logger = logging.getLogger(__name__)

# Tokenizer used for chunk sizing. cl100k_base is the encoding of OpenAI's
# text-embedding-3 models, so chunk sizes match what the embedding model sees.
TOKEN_ENCODING = "cl100k_base"
# Chunks with fewer tokens than this are fragments with too little context to be useful.
MIN_CHUNK_TOKENS = 30
# Separators tried in order: paragraphs, lines (e.g. table rows), sentences, words.
SEPARATORS = ["\n\n", "\n", ". ", " ", ""]

CHUNK_METADATA_KEYS = (
    "chunk_id",
    "source",
    "doc_title",
    "doc_type",
    "page",
    "chunk_index",
    "doc_hash",
    "section",
)

_SLUG_INVALID = re.compile(r"[^a-z0-9]+")


@lru_cache(maxsize=1)
def _encoding() -> tiktoken.Encoding:
    return tiktoken.get_encoding(TOKEN_ENCODING)


def count_tokens(text: str) -> int:
    """Return the number of tokens in `text` using the chunking tokenizer."""
    return len(_encoding().encode(text, disallowed_special=()))


def slugify(name: str) -> str:
    """Turn a file name into a stable, URL-safe slug ("SOP - Returns.pdf" -> "sop-returns")."""
    stem = Path(name).stem if name.lower().endswith(".pdf") else name
    slug = _SLUG_INVALID.sub("-", stem.lower()).strip("-")
    return slug or "document"


def make_chunk_id(doc_slug: str, page: int, chunk_index: int) -> str:
    """Build the deterministic chunk ID used as the vector store ID."""
    return f"{doc_slug}__p{page}__c{chunk_index}"


def build_splitter(settings: Settings | None = None) -> RecursiveCharacterTextSplitter:
    """Create the token-based splitter configured from Settings."""
    s = settings or get_settings()
    return RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        encoding_name=TOKEN_ENCODING,
        chunk_size=s.chunk_size_tokens,
        chunk_overlap=s.chunk_overlap_tokens,
        separators=SEPARATORS,
        keep_separator="end",
        add_start_index=True,
        strip_whitespace=True,
    )


def section_for(
    start: int, length: int, headings: Sequence[Heading], section_at_start: str | None
) -> str | None:
    """Return the section a chunk belongs to.

    Preference order: the last heading at or before the chunk start, then the section
    carried over from earlier pages, then the first heading inside the chunk.
    """
    before = [h for h in headings if h.offset <= start]
    if before:
        return before[-1].title
    if section_at_start:
        return section_at_start
    inside = [h for h in headings if start < h.offset < start + length]
    return inside[0].title if inside else None


def chunk_page(
    page: Document,
    doc_slug: str,
    splitter: RecursiveCharacterTextSplitter,
    min_tokens: int = MIN_CHUNK_TOKENS,
) -> list[Document]:
    """Split one page Document (from the loader) into chunk Documents."""
    meta = page.metadata
    headings: Sequence[Heading] = meta.get("headings") or ()
    pieces = splitter.create_documents([page.page_content])

    chunks: list[Document] = []
    dropped = 0
    for piece in pieces:
        text = piece.page_content
        if count_tokens(text) < min_tokens:
            dropped += 1
            continue
        start = piece.metadata.get("start_index", -1)
        if start < 0:  # text not found verbatim; fall back to a search
            start = max(page.page_content.find(text), 0)
        index = len(chunks)
        chunks.append(
            Document(
                page_content=text,
                metadata={
                    "chunk_id": make_chunk_id(doc_slug, meta["page"], index),
                    "source": meta["source"],
                    "doc_title": meta["doc_title"],
                    "doc_type": meta["doc_type"],
                    "page": meta["page"],
                    "chunk_index": index,
                    "doc_hash": meta["doc_hash"],
                    "section": section_for(
                        start, len(text), headings, meta.get("section_at_start")
                    ),
                },
            )
        )
    if dropped:
        logger.debug(
            "dropped small chunks",
            extra={"source": meta["source"], "page": meta["page"], "dropped": dropped},
        )
    return chunks


def chunk_documents(
    pages: Iterable[Document],
    doc_slug: str,
    settings: Settings | None = None,
    min_tokens: int = MIN_CHUNK_TOKENS,
) -> list[Document]:
    """Split all pages of one source document into chunks."""
    splitter = build_splitter(settings)
    chunks: list[Document] = []
    for page in pages:
        chunks.extend(chunk_page(page, doc_slug, splitter, min_tokens))
    return chunks
