"""Load PDFs into per-page documents with cleaned text.

Each PDF page becomes one LangChain `Document`. The text is rebuilt from PyMuPDF's layout
output so that it is clean enough to embed and quote:

- running headers and footers (lines that repeat in the top/bottom margin of more than
  half of the pages, ignoring digits such as page numbers) are removed;
- tables detected by PyMuPDF are rendered row by row as ``cell | cell | cell`` so that
  each row stays on one line instead of being scattered cell by cell;
- lines wrapped inside a paragraph are joined, words hyphenated across a line break are
  rejoined, and runs of whitespace are collapsed;
- blank pages (no extractable text) are skipped and logged.

Section headings (bold text that is larger than the body font, or bold numbered titles
such as ``4.2 Refund Approval``) are recorded per page with their character offset so the
chunker can assign a ``section`` to every chunk.

Unreadable files (encrypted, corrupted, zero pages) are skipped with a log entry instead of
failing the whole run.
"""

from __future__ import annotations

import contextlib
import hashlib
import logging
import re
from collections import Counter
from collections.abc import Iterable, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pymupdf
from langchain_core.documents import Document

logger = logging.getLogger(__name__)

# A line is a header/footer candidate only if it sits in the top or bottom margin band.
# This keeps repeated body text (e.g. "Yes"/"No" table cells) from being stripped.
MARGIN_BAND_RATIO = 0.08
# A margin line is treated as a running header/footer if it repeats on more than this
# share of the document's pages.
REPEAT_PAGE_RATIO = 0.5
# Headings longer than this are almost certainly bold body text, not titles.
MAX_HEADING_CHARS = 150
# A bold block counts as a heading if its font is at least this many points larger than
# the dominant body font size.
HEADING_SIZE_DELTA = 0.5

_BOLD_FLAG = 16  # PyMuPDF span flag bit for bold text
_NUMBERED_HEADING = re.compile(r"^(?:\d+(?:\.\d+)*\.?|[A-Z]\d*\.|Q\d+[a-z]?\.)\s+\S")
_PAGE_NUMBER_ONLY = re.compile(r"^(?:page\s*)?\d+(?:\s*(?:of|/)\s*\d+)?$", re.IGNORECASE)
_HYPHEN_BREAK = re.compile(r"(?<=[a-z])-$")
_WHITESPACE = re.compile(r"\s+")

DOC_TYPE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("product_guide", re.compile(r"product[\s_-]*guide|manual|user[\s_-]*guide", re.I)),
    ("sop", re.compile(r"\bsop\b|standard[\s_-]*operating|procedure", re.I)),
    ("faq", re.compile(r"\bfaqs?\b", re.I)),
    ("policy", re.compile(r"polic(?:y|ies)", re.I)),
)
DEFAULT_DOC_TYPE = "other"


class PdfLoadError(Exception):
    """Raised when a PDF cannot be opened or read (encrypted, corrupted, empty)."""


@dataclass(frozen=True)
class Heading:
    """A section heading found on a page, with its offset in the cleaned page text."""

    offset: int
    title: str


@dataclass
class _Line:
    text: str
    bbox: tuple[float, float, float, float]
    size: float
    bold: bool


@dataclass
class _Block:
    lines: list[_Line]
    bbox: tuple[float, float, float, float]


@dataclass
class _Element:
    """A unit of page content in reading order: a paragraph, a heading or a table."""

    y0: float
    x0: float
    text: str
    is_heading: bool = False


@dataclass
class _RawPage:
    number: int  # 1-based
    height: float
    blocks: list[_Block]
    tables: list[tuple[tuple[float, float, float, float], list[str]]] = field(default_factory=list)


def file_sha256(path: Path) -> str:
    """Return the hex SHA-256 digest of a file's bytes."""
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 20), b""):
            digest.update(chunk)
    return digest.hexdigest()


def infer_doc_type(path: Path, root: Path | None = None) -> str:
    """Infer the document type from the file name, falling back to parent directory names."""
    candidates = [path.stem]
    if root is not None:
        with contextlib.suppress(ValueError):  # path outside root: file name only
            candidates.extend(reversed(path.parent.relative_to(root).parts))
    for candidate in candidates:
        for doc_type, pattern in DOC_TYPE_PATTERNS:
            if pattern.search(candidate):
                return doc_type
    return DEFAULT_DOC_TYPE


def _collapse(text: str) -> str:
    return _WHITESPACE.sub(" ", text).strip()


def _join_lines(lines: Iterable[str]) -> str:
    """Join wrapped lines of one paragraph, repairing words hyphenated at a line break."""
    out = ""
    for raw in lines:
        line = _collapse(raw)
        if not line:
            continue
        if not out:
            out = line
        elif _HYPHEN_BREAK.search(out) and line[0].islower():
            out = out[:-1] + line
        else:
            out = f"{out} {line}"
    return out


def _margin_key(text: str) -> str:
    """Normalise a margin line so that 'Page 3 of 5' and 'Page 4 of 5' compare equal."""
    return re.sub(r"\d+", "#", _collapse(text).lower())


def _in_margin(bbox: tuple[float, float, float, float], height: float) -> bool:
    band = height * MARGIN_BAND_RATIO
    return bbox[3] <= band or bbox[1] >= height - band


def _center_inside(
    bbox: tuple[float, float, float, float], rect: tuple[float, float, float, float]
) -> bool:
    cx = (bbox[0] + bbox[2]) / 2
    cy = (bbox[1] + bbox[3]) / 2
    return rect[0] <= cx <= rect[2] and rect[1] <= cy <= rect[3]


def _read_raw_page(page: pymupdf.Page) -> _RawPage:
    raw = _RawPage(number=page.number + 1, height=page.rect.height, blocks=[])

    try:
        tables = page.find_tables().tables
    except Exception:  # table detection is best effort; fall back to plain text
        logger.warning("table detection failed", extra={"page": raw.number}, exc_info=True)
        tables = []
    for table in tables:
        grid = [
            [
                _collapse(page.get_text("text", clip=cell)) if cell is not None else ""
                for cell in row.cells
            ]
            for row in table.rows
        ]
        grid = [row for row in grid if any(row)]
        if not grid:
            continue
        # Drop columns that are empty in every row (artifacts of merged or ruled cells).
        width = max(len(row) for row in grid)
        keep = [c for c in range(width) if any(c < len(row) and row[c] for row in grid)]
        rows = [" | ".join(row[c] if c < len(row) else "" for c in keep) for row in grid]
        raw.tables.append((tuple(table.bbox), rows))

    for block in page.get_text("dict")["blocks"]:
        if block.get("type") != 0:
            continue
        lines: list[_Line] = []
        for line in block["lines"]:
            spans = [s for s in line["spans"] if s["text"].strip()]
            if not spans:
                continue
            text = "".join(s["text"] for s in line["spans"])
            size = max(s["size"] for s in spans)
            bold = all((s["flags"] & _BOLD_FLAG) or "bold" in s["font"].lower() for s in spans)
            lines.append(_Line(text=text, bbox=tuple(line["bbox"]), size=size, bold=bold))
        if lines:
            raw.blocks.append(_Block(lines=lines, bbox=tuple(block["bbox"])))
    return raw


def _repeated_margin_keys(pages: Sequence[_RawPage]) -> set[str]:
    """Return normalised margin lines that repeat on more than REPEAT_PAGE_RATIO of pages."""
    if len(pages) < 2:
        return set()
    counts: Counter[str] = Counter()
    for page in pages:
        keys = {
            _margin_key(line.text)
            for block in page.blocks
            for line in block.lines
            if _in_margin(line.bbox, page.height)
        }
        counts.update(keys)
    threshold = len(pages) * REPEAT_PAGE_RATIO
    return {key for key, count in counts.items() if count > threshold}


def _body_font_size(pages: Sequence[_RawPage]) -> float:
    """Return the dominant font size, weighted by characters, across the document."""
    sizes: Counter[float] = Counter()
    for page in pages:
        for block in page.blocks:
            for line in block.lines:
                sizes[round(line.size, 1)] += len(line.text)
    return sizes.most_common(1)[0][0] if sizes else 0.0


def _is_heading(text: str, lines: Sequence[_Line], body_size: float) -> bool:
    if not text or len(text) > MAX_HEADING_CHARS or not all(line.bold for line in lines):
        return False
    larger = max(line.size for line in lines) >= body_size + HEADING_SIZE_DELTA
    return larger or bool(_NUMBERED_HEADING.match(text))


def _page_elements(
    page: _RawPage, header_footer_keys: set[str], body_size: float
) -> tuple[list[_Element], int]:
    """Build the ordered content elements of a page; also return removed margin line count."""
    elements: list[_Element] = []
    removed = 0
    table_boxes = [bbox for bbox, _ in page.tables]

    for block in page.blocks:
        kept: list[_Line] = []
        for line in block.lines:
            if _in_margin(line.bbox, page.height) and (
                _margin_key(line.text) in header_footer_keys
                or _PAGE_NUMBER_ONLY.match(_collapse(line.text))
            ):
                removed += 1
                continue
            if any(_center_inside(line.bbox, box) for box in table_boxes):
                continue
            kept.append(line)
        if not kept:
            continue
        text = _join_lines(line.text for line in kept)
        if not text:
            continue
        y0 = min(line.bbox[1] for line in kept)
        x0 = min(line.bbox[0] for line in kept)
        elements.append(
            _Element(y0=y0, x0=x0, text=text, is_heading=_is_heading(text, kept, body_size))
        )

    for bbox, rows in page.tables:
        elements.append(_Element(y0=bbox[1], x0=bbox[0], text="\n".join(rows)))

    elements.sort(key=lambda e: (round(e.y0, 1), e.x0))
    return elements, removed


def _assemble(elements: Sequence[_Element], doc_title: str) -> tuple[str, list[Heading]]:
    parts: list[str] = []
    headings: list[Heading] = []
    offset = 0
    for element in elements:
        if parts:
            offset += 2  # the "\n\n" separator
        if element.is_heading and element.text.casefold() != doc_title.casefold():
            headings.append(Heading(offset=offset, title=element.text))
        parts.append(element.text)
        offset += len(element.text)
    return "\n\n".join(parts), headings


def _open_pdf(path: Path) -> pymupdf.Document:
    try:
        pdf = pymupdf.open(path)
    except Exception as exc:
        raise PdfLoadError(f"cannot open PDF: {exc}") from exc
    if pdf.needs_pass:
        pdf.close()
        raise PdfLoadError("PDF is encrypted with a password")
    if pdf.page_count == 0:
        pdf.close()
        raise PdfLoadError("PDF has no pages")
    return pdf


def load_pdf(path: Path, root: Path | None = None) -> list[Document]:
    """Load one PDF into a list of per-page Documents (blank pages are omitted).

    Each Document's metadata holds: source, doc_title, doc_type, page (1-based), doc_hash,
    total_pages, headings (list of `Heading` found on the page, in order) and
    section_at_start (the last heading seen on an earlier page, or None).

    Raises:
        PdfLoadError: if the file cannot be read or opened, is password protected, has no
            pages or its pages cannot be read.
    """
    try:
        doc_hash = file_sha256(path)
    except OSError as exc:
        raise PdfLoadError(f"cannot read file: {exc}") from exc
    with _open_pdf(path) as pdf:
        doc_title = _collapse((pdf.metadata or {}).get("title") or "") or path.stem
        try:
            raw_pages = [_read_raw_page(page) for page in pdf]
        except Exception as exc:
            raise PdfLoadError(f"cannot read PDF pages: {exc}") from exc
        total_pages = pdf.page_count

    header_footer_keys = _repeated_margin_keys(raw_pages)
    body_size = _body_font_size(raw_pages)
    doc_type = infer_doc_type(path, root)

    documents: list[Document] = []
    current_section: str | None = None
    blank_pages: list[int] = []
    removed_lines = 0
    for raw in raw_pages:
        elements, removed = _page_elements(raw, header_footer_keys, body_size)
        removed_lines += removed
        text, headings = _assemble(elements, doc_title)
        if not text.strip():
            blank_pages.append(raw.number)
            continue
        metadata: dict[str, Any] = {
            "source": path.name,
            "doc_title": doc_title,
            "doc_type": doc_type,
            "page": raw.number,
            "doc_hash": doc_hash,
            "total_pages": total_pages,
            "headings": headings,
            "section_at_start": current_section,
        }
        documents.append(Document(page_content=text, metadata=metadata))
        if headings:
            current_section = headings[-1].title

    if blank_pages:
        logger.info(
            "skipped blank pages",
            extra={"source": path.name, "pages": blank_pages},
        )
    if not documents:
        logger.warning(
            "no extractable text in PDF (scanned or image-only?)",
            extra={"source": path.name, "total_pages": total_pages},
        )
    logger.debug(
        "loaded pdf",
        extra={
            "source": path.name,
            "pages": len(documents),
            "header_footer_lines_removed": removed_lines,
        },
    )
    return documents


def find_pdfs(pdf_dir: Path) -> list[Path]:
    """Return all PDF files under `pdf_dir` (recursive), sorted for deterministic output."""
    return sorted(
        (p for p in pdf_dir.rglob("*") if p.is_file() and p.suffix.lower() == ".pdf"),
        key=lambda p: p.relative_to(pdf_dir).as_posix(),
    )
