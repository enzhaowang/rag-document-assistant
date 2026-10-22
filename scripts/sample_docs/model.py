"""Content model for the fictional Lumora Home Systems sample documents.

Documents are described as plain data (a list of blocks) so that the content modules
stay readable and the renderer in `scripts/generate_sample_pdfs.py` owns all layout.

Inline markup supported in text: `**bold**`. Everything else is literal text.
"""

from dataclasses import dataclass, field
from typing import Literal

DocType = Literal["product_guide", "sop", "faq", "policy"]
FactKind = Literal["text", "table", "cross-page"]


@dataclass(frozen=True)
class Heading:
    text: str
    level: int  # 1, 2 or 3


@dataclass(frozen=True)
class Para:
    text: str


@dataclass(frozen=True)
class Bullets:
    items: tuple[str, ...]


@dataclass(frozen=True)
class Steps:
    items: tuple[str, ...]
    start: int = 1


@dataclass(frozen=True)
class Table:
    header: tuple[str, ...]
    rows: tuple[tuple[str, ...], ...]
    # Relative column widths; they are normalised to the frame width when rendering.
    widths: tuple[float, ...] | None = None
    caption: str | None = None


@dataclass(frozen=True)
class Note:
    text: str
    label: str = "Note"


@dataclass(frozen=True)
class PageBreak:
    pass


Block = Heading | Para | Bullets | Steps | Table | Note | PageBreak


@dataclass(frozen=True)
class Fact:
    """A hard fact embedded in a document, used later to write evaluation questions.

    `needles` are literal snippets of the rendered text. The generator locates them in
    the finished PDF to compute page numbers, so they must be unique within the document.
    A `cross-page` fact has two needles: the first must sit on page N, the second on N+1.
    """

    id: str
    statement: str
    needles: tuple[str, ...]
    kind: FactKind = "text"
    tags: tuple[str, ...] = ()


@dataclass(frozen=True)
class SampleDoc:
    filename: str
    title: str
    doc_type: DocType
    doc_number: str
    revision: str
    effective_date: str
    owner: str
    audience: str
    purpose: str
    blocks: tuple[Block, ...]
    facts: tuple[Fact, ...] = field(default_factory=tuple)


# Small constructors keep the content modules compact.
def h1(text: str) -> Heading:
    return Heading(text, 1)


def h2(text: str) -> Heading:
    return Heading(text, 2)


def h3(text: str) -> Heading:
    return Heading(text, 3)


def p(text: str) -> Para:
    return Para(text)


def bullets(*items: str) -> Bullets:
    return Bullets(tuple(items))


def steps(*items: str, start: int = 1) -> Steps:
    return Steps(tuple(items), start)


def table(
    header: tuple[str, ...],
    rows: list[tuple[str, ...]],
    widths: tuple[float, ...] | None = None,
    caption: str | None = None,
) -> Table:
    return Table(header, tuple(rows), widths, caption)


def note(text: str, label: str = "Note") -> Note:
    return Note(text, label)


def page_break() -> PageBreak:
    return PageBreak()


def fact(
    fact_id: str,
    statement: str,
    *needles: str,
    kind: FactKind = "text",
    tags: tuple[str, ...] = (),
) -> Fact:
    return Fact(fact_id, statement, tuple(needles), kind, tags)
