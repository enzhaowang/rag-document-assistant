"""Generate the fictional sample PDF knowledge base into data/pdfs/.

The documents belong to Lumora Home Systems, a made-up smart-home company. They imitate
a real internal knowledge base: four product guides, four SOPs, three FAQs and one
warranty policy, with tables, numbered procedures, multi-level headings and running
headers/footers.

After rendering, every embedded fact (see `scripts/sample_docs/`) is located in the
finished PDFs with PyMuPDF and `FACTS.md` is written with the verified file name and
page number(s). The run fails if a fact cannot be found exactly where it is expected,
so FACTS.md cannot drift from the PDFs.

Output is deterministic: running the script twice produces byte-identical files.

Usage:
    python scripts/generate_sample_pdfs.py [--out-dir DIR]
"""

import argparse
import re
import sys
from collections.abc import Sequence
from dataclasses import dataclass
from html import escape
from pathlib import Path
from typing import Any

import pymupdf
from reportlab.lib import colors
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import inch
from reportlab.pdfgen import canvas
from reportlab.platypus import Flowable, Paragraph, SimpleDocTemplate, Spacer
from reportlab.platypus import PageBreak as RLPageBreak
from reportlab.platypus import Table as RLTable
from reportlab.platypus import TableStyle as RLTableStyle

# Support `python scripts/generate_sample_pdfs.py` as well as `python -m scripts.<name>`.
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import get_settings  # noqa: E402
from scripts.sample_docs import ALL_DOCS  # noqa: E402
from scripts.sample_docs.model import (  # noqa: E402
    Block,
    Bullets,
    Fact,
    Heading,
    Note,
    PageBreak,
    Para,
    SampleDoc,
    Steps,
    Table,
)

COMPANY = "Lumora Home Systems"
FACTS_FILENAME = "FACTS.md"
PAGE_SIZE = LETTER
MARGIN_X = 1.0 * inch
MARGIN_TOP = 0.95 * inch
MARGIN_BOTTOM = 0.85 * inch
FRAME_WIDTH = PAGE_SIZE[0] - 2 * MARGIN_X

INK = colors.HexColor("#1F2933")
ACCENT = colors.HexColor("#0B6E69")
MUTED = colors.HexColor("#6B7780")
RULE = colors.HexColor("#C9D2D6")
HEADER_FILL = colors.HexColor("#E3EFEE")
NOTE_FILL = colors.HexColor("#F4F7F8")

DOC_TYPE_LABELS = {
    "product_guide": "Product Guide",
    "sop": "Standard Operating Procedure",
    "faq": "Frequently Asked Questions",
    "policy": "Policy",
}


# ---------------------------------------------------------------------------- styles


def _style(name: str, **overrides: Any) -> ParagraphStyle:
    options: dict[str, Any] = {
        "fontName": "Helvetica",
        "fontSize": 10.5,
        "leading": 15,
        "textColor": INK,
        "spaceAfter": 6,
    }
    options.update(overrides)
    return ParagraphStyle(name, **options)


STYLES: dict[str, ParagraphStyle] = {
    "kicker": _style("kicker", fontSize=9, textColor=ACCENT, fontName="Helvetica-Bold"),
    "title": _style("title", fontName="Helvetica-Bold", fontSize=20, leading=25, spaceAfter=10),
    "body": _style("body"),
    "h1": _style(
        "h1",
        fontName="Helvetica-Bold",
        fontSize=14,
        leading=18,
        textColor=ACCENT,
        spaceBefore=12,
        spaceAfter=6,
        keepWithNext=1,
    ),
    "h2": _style(
        "h2",
        fontName="Helvetica-Bold",
        fontSize=11.5,
        leading=15,
        spaceBefore=9,
        spaceAfter=4,
        keepWithNext=1,
    ),
    "h3": _style(
        "h3",
        fontName="Helvetica-BoldOblique",
        fontSize=10,
        leading=14,
        spaceBefore=6,
        spaceAfter=3,
        keepWithNext=1,
    ),
    "list": _style("list", leftIndent=18, bulletIndent=4, spaceAfter=3),
    "cell": _style("cell", fontSize=9.2, leading=12, spaceAfter=0),
    "cell_head": _style("cell_head", fontSize=9.2, leading=12, fontName="Helvetica-Bold"),
    "caption": _style("caption", fontSize=8.5, leading=11, textColor=MUTED, spaceBefore=2),
    "note": _style("note", fontSize=9.8, leading=13.5, spaceAfter=0),
}

_BOLD = re.compile(r"\*\*(.+?)\*\*")


def _markup(text: str) -> str:
    """Escape text for reportlab and translate `**bold**` into <b> tags."""
    return _BOLD.sub(r"<b>\1</b>", escape(text, quote=False))


def _plain(text: str) -> str:
    return _BOLD.sub(r"\1", text)


# --------------------------------------------------------------------------- render


class _Rule(Flowable):
    """A thin horizontal rule spanning the frame."""

    def __init__(self, width: float, color: colors.Color = RULE, gap: float = 6) -> None:
        super().__init__()
        self.width = width
        self.color = color
        self.gap = gap

    def wrap(self, avail_width: float, avail_height: float) -> tuple[float, float]:
        return self.width, self.gap * 2

    def draw(self) -> None:
        self.canv.setStrokeColor(self.color)
        self.canv.setLineWidth(0.6)
        self.canv.line(0, self.gap, self.width, self.gap)


def _table(header: Sequence[str], rows: Sequence[Sequence[str]], widths: Sequence[float] | None):
    ncols = len(header)
    for row in rows:
        if len(row) != ncols:
            raise ValueError(f"table row has {len(row)} cells, expected {ncols}: {row}")
    rel = list(widths) if widths else [1.0] * ncols
    col_widths = [FRAME_WIDTH * w / sum(rel) for w in rel]
    data = [[Paragraph(_markup(h), STYLES["cell_head"]) for h in header]]
    data += [[Paragraph(_markup(c), STYLES["cell"]) for c in row] for row in rows]
    tbl = RLTable(data, colWidths=col_widths, repeatRows=1, hAlign="LEFT")
    tbl.setStyle(
        RLTableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), HEADER_FILL),
                ("GRID", (0, 0), (-1, -1), 0.5, RULE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("TOPPADDING", (0, 0), (-1, -1), 3.5),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3.5),
                ("LEFTPADDING", (0, 0), (-1, -1), 5),
                ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ]
        )
    )
    return tbl


def _render_block(block: Block) -> list[Flowable]:
    if isinstance(block, Heading):
        return [Paragraph(_markup(block.text), STYLES[f"h{block.level}"])]
    if isinstance(block, Para):
        return [Paragraph(_markup(block.text), STYLES["body"])]
    if isinstance(block, Bullets):
        return [
            Paragraph(_markup(item), STYLES["list"], bulletText="•") for item in block.items
        ] + [Spacer(1, 3)]
    if isinstance(block, Steps):
        return [
            Paragraph(_markup(item), STYLES["list"], bulletText=f"{n}.")
            for n, item in enumerate(block.items, start=block.start)
        ] + [Spacer(1, 3)]
    if isinstance(block, Table):
        out: list[Flowable] = [_table(block.header, block.rows, block.widths)]
        if block.caption:
            out.append(Paragraph(_markup(block.caption), STYLES["caption"]))
        out.append(Spacer(1, 8))
        return out
    if isinstance(block, Note):
        text = f"<b>{escape(block.label)}:</b> {_markup(block.text)}"
        box = RLTable([[Paragraph(text, STYLES["note"])]], colWidths=[FRAME_WIDTH])
        box.setStyle(
            RLTableStyle(
                [
                    ("BACKGROUND", (0, 0), (-1, -1), NOTE_FILL),
                    ("LINEBEFORE", (0, 0), (0, -1), 2.5, ACCENT),
                    ("TOPPADDING", (0, 0), (-1, -1), 6),
                    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
                    ("LEFTPADDING", (0, 0), (-1, -1), 9),
                ]
            )
        )
        return [box, Spacer(1, 8)]
    if isinstance(block, PageBreak):
        return [RLPageBreak()]
    raise TypeError(f"unsupported block: {block!r}")


def _front_matter(doc: SampleDoc) -> list[Flowable]:
    control = [
        ("Document number", doc.doc_number),
        ("Revision", doc.revision),
        ("Effective date", doc.effective_date),
        ("Document owner", doc.owner),
        ("Audience", doc.audience),
        ("Classification", "Internal - do not distribute outside Lumora"),
    ]
    tbl = RLTable(
        [
            [Paragraph(f"<b>{escape(k)}</b>", STYLES["cell"]), Paragraph(escape(v), STYLES["cell"])]
            for k, v in control
        ],
        colWidths=[FRAME_WIDTH * 0.28, FRAME_WIDTH * 0.72],
        hAlign="LEFT",
    )
    tbl.setStyle(
        RLTableStyle(
            [
                ("BACKGROUND", (0, 0), (0, -1), HEADER_FILL),
                ("GRID", (0, 0), (-1, -1), 0.5, RULE),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]
        )
    )
    return [
        Paragraph(escape(DOC_TYPE_LABELS[doc.doc_type].upper()), STYLES["kicker"]),
        Paragraph(escape(doc.title), STYLES["title"]),
        tbl,
        Spacer(1, 10),
        Paragraph(f"<b>Purpose.</b> {_markup(doc.purpose)}", STYLES["body"]),
        _Rule(FRAME_WIDTH),
    ]


def _canvas_class(doc: SampleDoc) -> type[canvas.Canvas]:
    """Build a canvas that draws running headers/footers with "Page X of Y"."""

    class _NumberedCanvas(canvas.Canvas):
        def __init__(self, *args: Any, **kwargs: Any) -> None:
            super().__init__(*args, **kwargs)
            self._pages: list[dict[str, Any]] = []

        def showPage(self) -> None:  # noqa: N802 - reportlab API name
            self._pages.append(dict(self.__dict__))
            self._startPage()

        def save(self) -> None:
            total = len(self._pages)
            for state in self._pages:
                self.__dict__.update(state)
                self._decorate(total)
                super().showPage()
            super().save()

        def _decorate(self, total: int) -> None:
            width, height = PAGE_SIZE
            self.saveState()
            self.setFont("Helvetica-Bold", 8)
            self.setFillColor(ACCENT)
            self.drawString(MARGIN_X, height - 0.55 * inch, COMPANY)
            self.setFont("Helvetica", 8)
            self.setFillColor(MUTED)
            self.drawRightString(
                width - MARGIN_X, height - 0.55 * inch, f"{doc.doc_number} | Rev {doc.revision}"
            )
            self.setStrokeColor(RULE)
            self.setLineWidth(0.6)
            self.line(MARGIN_X, height - 0.62 * inch, width - MARGIN_X, height - 0.62 * inch)
            self.line(MARGIN_X, 0.62 * inch, width - MARGIN_X, 0.62 * inch)
            self.drawString(MARGIN_X, 0.45 * inch, "Internal use only - Confidential")
            self.drawRightString(
                width - MARGIN_X, 0.45 * inch, f"Page {self._pageNumber} of {total}"
            )
            self.restoreState()

    return _NumberedCanvas


def render_pdf(doc: SampleDoc, path: Path) -> None:
    """Render one document to `path` with title/author/subject metadata."""
    template = SimpleDocTemplate(
        str(path),
        pagesize=PAGE_SIZE,
        leftMargin=MARGIN_X,
        rightMargin=MARGIN_X,
        topMargin=MARGIN_TOP,
        bottomMargin=MARGIN_BOTTOM,
        title=doc.title,
        author=f"{COMPANY} - {doc.owner}",
        subject=f"{DOC_TYPE_LABELS[doc.doc_type]} {doc.doc_number}",
        keywords=f"lumora, {doc.doc_type}, {doc.doc_number}",
        creator=f"{COMPANY} Document Control",
        producer=f"{COMPANY} Document Control",
        invariant=1,  # fixed timestamps and IDs -> byte-identical output on every run
    )
    story: list[Flowable] = _front_matter(doc)
    for block in doc.blocks:
        story.extend(_render_block(block))
    template.build(story, canvasmaker=_canvas_class(doc))


# ------------------------------------------------------------------------ fact check


@dataclass(frozen=True)
class LocatedFact:
    fact: Fact
    doc: SampleDoc
    pages: tuple[int, ...]  # 1-based, as shown in a PDF reader


class FactLocationError(RuntimeError):
    """Raised when an embedded fact cannot be located unambiguously in its PDF."""


def _normalise(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _pages_containing(page_texts: Sequence[str], needle: str) -> list[int]:
    target = _normalise(_plain(needle))
    return [i + 1 for i, text in enumerate(page_texts) if target in text]


def locate_facts(doc: SampleDoc, pdf_path: Path) -> list[LocatedFact]:
    """Find the page(s) of every fact in `doc` by searching the rendered PDF text."""
    with pymupdf.open(pdf_path) as pdf:
        page_texts = [_normalise(page.get_text("text")) for page in pdf]

    located: list[LocatedFact] = []
    for fct in doc.facts:
        hits = [_pages_containing(page_texts, n) for n in fct.needles]
        for needle, pages in zip(fct.needles, hits, strict=True):
            if len(pages) != 1:
                raise FactLocationError(
                    f"{fct.id}: needle {needle!r} found on pages {pages} of {doc.filename}; "
                    "expected exactly one page"
                )
        pages = tuple(h[0] for h in hits)
        if fct.kind == "cross-page":
            if len(pages) != 2 or pages[1] != pages[0] + 1:
                raise FactLocationError(
                    f"{fct.id}: cross-page fact must start on page N and end on page N+1, "
                    f"got pages {pages} in {doc.filename}"
                )
        elif len(set(pages)) != 1:
            raise FactLocationError(
                f"{fct.id}: needles are on different pages {pages} in {doc.filename}"
            )
        located.append(LocatedFact(fct, doc, tuple(sorted(set(pages)))))
    return located


# ------------------------------------------------------------------------- FACTS.md


def _cell(text: str) -> str:
    return _plain(text).replace("|", "\\|")


def render_facts_markdown(located: Sequence[LocatedFact], page_counts: dict[str, int]) -> str:
    total_pages = sum(page_counts.values())
    lines = [
        "# Sample Knowledge Base: Embedded Facts",
        "",
        "Generated by `scripts/generate_sample_pdfs.py`. Do not edit by hand: page numbers are",
        "located automatically in the rendered PDFs (1-based, as shown in a PDF reader).",
        "",
        "All content describes **Lumora Home Systems**, a fictional company. Any resemblance",
        "to real companies, products or people is coincidental.",
        "",
        f"- Documents: {len(page_counts)}",
        f"- Pages: {total_pages}",
        f"- Facts: {len(located)}",
        "",
        "Fact kinds: `text` = stated in running text, `table` = stated in a table row,",
        "`cross-page` = the statement starts on one page and finishes on the next.",
        "Tag `confusable` marks facts that differ between similar products (for example",
        "the T2 and T3 thermostats) and are useful for testing retrieval precision.",
        "",
        "## Documents",
        "",
        "| File | Type | Pages |",
        "|---|---|---|",
    ]
    for doc in ALL_DOCS:
        lines.append(f"| {doc.filename} | {doc.doc_type} | {page_counts[doc.filename]} |")
    lines += [
        "",
        "## Facts",
        "",
        "| ID | Fact | File | Page(s) | Kind | Tags |",
        "|---|---|---|---|---|---|",
    ]
    for item in located:
        pages = "-".join(str(n) for n in item.pages)
        tags = ", ".join(item.fact.tags)
        lines.append(
            f"| {item.fact.id} | {_cell(item.fact.statement)} | {item.doc.filename} | "
            f"{pages} | {item.fact.kind} | {tags} |"
        )
    lines.append("")
    return "\n".join(lines)


# ------------------------------------------------------------------------------ main


def generate(out_dir: Path) -> tuple[list[LocatedFact], dict[str, int]]:
    """Render every sample document into `out_dir` and write FACTS.md next to them."""
    out_dir.mkdir(parents=True, exist_ok=True)
    located: list[LocatedFact] = []
    page_counts: dict[str, int] = {}
    seen_ids: set[str] = set()
    for doc in ALL_DOCS:
        path = out_dir / doc.filename
        render_pdf(doc, path)
        with pymupdf.open(path) as pdf:
            page_counts[doc.filename] = pdf.page_count
        for item in locate_facts(doc, path):
            if item.fact.id in seen_ids:
                raise FactLocationError(f"duplicate fact id {item.fact.id}")
            seen_ids.add(item.fact.id)
            located.append(item)
    (out_dir / FACTS_FILENAME).write_text(
        render_facts_markdown(located, page_counts), encoding="utf-8"
    )
    return located, page_counts


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--out-dir",
        type=Path,
        default=None,
        help="output directory (default: PDF_DIR from settings)",
    )
    args = parser.parse_args(argv)
    out_dir: Path = args.out_dir or get_settings().pdf_dir

    located, page_counts = generate(out_dir)
    for name, count in page_counts.items():
        print(f"{count:>3} pages  {name}")
    print(
        f"Wrote {len(page_counts)} PDFs ({sum(page_counts.values())} pages) and "
        f"{FACTS_FILENAME} ({len(located)} facts) to {out_dir}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
