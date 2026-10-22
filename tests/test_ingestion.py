"""Tests for the ingestion pipeline: PDF loading, cleaning, chunking and metadata."""

import re
from pathlib import Path

import pymupdf
import pytest

from app.config import Settings
from app.ingestion.chunker import (
    CHUNK_METADATA_KEYS,
    MIN_CHUNK_TOKENS,
    count_tokens,
    make_chunk_id,
    section_for,
    slugify,
)
from app.ingestion.loader import Heading, PdfLoadError, infer_doc_type, load_pdf
from app.ingestion.pipeline import load_and_chunk, main, run

HEADER = "Acme Test Co | DOC-TST-001 Rev 2"
FOOTER = "Internal use only"
FILLER = (
    "The returns desk reviews every request within five business days and records each "
    "decision in the ticket together with the order number, the delivery date and the "
    "payment method used. "
)


def _write_body(page: pymupdf.Page, top: float, text: str, bottom: float = 700) -> None:
    rect = pymupdf.Rect(72, top, 540, bottom)
    assert page.insert_textbox(rect, text, fontsize=10.5) >= 0, "text did not fit"


def _draw_table(page: pymupdf.Page, top: float, rows: list[tuple[str, str]]) -> None:
    xs = [72, 200, 400]
    ys = [top + 20 * i for i in range(len(rows) + 1)]
    for y in ys:
        page.draw_line((xs[0], y), (xs[-1], y))
    for x in xs:
        page.draw_line((x, ys[0]), (x, ys[-1]))
    for i, row in enumerate(rows):
        for j, cell in enumerate(row):
            page.insert_text((xs[j] + 4, ys[i] + 14), cell, fontsize=9)


def build_sample_pdf(path: Path, title: str = "Returns Handbook") -> Path:
    """Build a 4-page PDF: headings, a blank page, a table and running header/footer."""
    pdf = pymupdf.open()
    total = 4
    for number in range(1, total + 1):
        page = pdf.new_page(width=612, height=792)
        page.insert_text((72, 40), HEADER, fontsize=8)
        page.insert_text((72, 770), f"{FOOTER}    Page {number} of {total}", fontsize=8)
        if number == 1:
            page.insert_text((72, 100), title, fontsize=20, fontname="hebo")
            page.insert_text((72, 140), "1. Overview", fontsize=14, fontname="hebo")
            _write_body(page, 150, FILLER * 3, bottom=330)
            page.insert_text((72, 360), "1.1 Scope", fontsize=11.5, fontname="hebo")
            _write_body(
                page,
                370,
                "Customers must quote the order number and the hyphen-\n"
                "ated serial number printed on the device label. " + FILLER * 2,
            )
        elif number == 2:
            continue  # only header and footer: a blank page after cleaning
        elif number == 3:
            _write_body(page, 80, FILLER * 2 + "Refunds above $250 need Team Lead approval.")
        else:
            page.insert_text((72, 100), "2. Error Codes", fontsize=14, fontname="hebo")
            _write_body(page, 110, FILLER, bottom=200)
            _draw_table(
                page,
                220,
                [("Code", "Meaning"), ("E1", "Sensor failure"), ("E2", "No heat detected")],
            )
    pdf.set_metadata({"title": title})
    pdf.save(path)
    pdf.close()
    return path


@pytest.fixture
def small_settings() -> Settings:
    return Settings(_env_file=None, chunk_size_tokens=60, chunk_overlap_tokens=10)


@pytest.fixture
def pdf_dir(tmp_path: Path) -> Path:
    directory = tmp_path / "pdfs"
    directory.mkdir()
    build_sample_pdf(directory / "SOP - Returns Handbook.pdf")
    return directory


# ----------------------------------------------------------------------------- loader


def test_loader_page_numbers_are_one_based_and_blank_pages_skipped(pdf_dir: Path) -> None:
    pages = load_pdf(pdf_dir / "SOP - Returns Handbook.pdf", root=pdf_dir)
    assert [p.metadata["page"] for p in pages] == [1, 3, 4]
    assert all(p.metadata["total_pages"] == 4 for p in pages)


def test_loader_removes_running_header_and_footer(pdf_dir: Path) -> None:
    pages = load_pdf(pdf_dir / "SOP - Returns Handbook.pdf", root=pdf_dir)
    for page in pages:
        assert "Acme Test Co" not in page.page_content
        assert FOOTER not in page.page_content
        assert not re.search(r"Page \d+ of \d+", page.page_content)


def test_loader_cleans_text(pdf_dir: Path) -> None:
    first = load_pdf(pdf_dir / "SOP - Returns Handbook.pdf", root=pdf_dir)[0]
    text = first.page_content
    assert "hyphenated serial number" in text
    assert "  " not in text
    # Wrapped lines of one paragraph are joined into a single line.
    assert "the order number, the delivery date and the payment method" in text


def test_loader_metadata_and_headings(pdf_dir: Path) -> None:
    pages = load_pdf(pdf_dir / "SOP - Returns Handbook.pdf", root=pdf_dir)
    first, third, fourth = pages
    meta = first.metadata
    assert meta["source"] == "SOP - Returns Handbook.pdf"
    assert meta["doc_title"] == "Returns Handbook"
    assert meta["doc_type"] == "sop"
    assert re.fullmatch(r"[0-9a-f]{64}", meta["doc_hash"])
    # The document title is not a section; numbered bold titles are.
    assert [h.title for h in meta["headings"]] == ["1. Overview", "1.1 Scope"]
    assert first.page_content[meta["headings"][1].offset :].startswith("1.1 Scope")
    assert third.metadata["headings"] == []
    assert third.metadata["section_at_start"] == "1.1 Scope"
    assert [h.title for h in fourth.metadata["headings"]] == ["2. Error Codes"]


def test_loader_renders_table_rows_on_one_line(pdf_dir: Path) -> None:
    fourth = load_pdf(pdf_dir / "SOP - Returns Handbook.pdf", root=pdf_dir)[-1]
    lines = fourth.page_content.splitlines()
    assert "Code | Meaning" in lines
    assert "E1 | Sensor failure" in lines
    assert "E2 | No heat detected" in lines


def test_title_falls_back_to_file_stem(tmp_path: Path) -> None:
    path = tmp_path / "FAQ - Billing.pdf"
    pdf = pymupdf.open()
    page = pdf.new_page()
    _write_body(page, 80, FILLER)
    pdf.save(path)
    pdf.close()
    (page_doc,) = load_pdf(path)
    assert page_doc.metadata["doc_title"] == "FAQ - Billing"
    assert page_doc.metadata["doc_type"] == "faq"


@pytest.mark.parametrize(
    ("relative", "expected"),
    [
        ("Product Guide - Lumora Thermostat T2.pdf", "product_guide"),
        ("SOP - RMA Process.pdf", "sop"),
        ("FAQ - Shipping and Delivery.pdf", "faq"),
        ("Policy - Limited Warranty.pdf", "policy"),
        ("faq/Shipping.pdf", "faq"),
        ("misc/Price List.pdf", "other"),
    ],
)
def test_infer_doc_type(tmp_path: Path, relative: str, expected: str) -> None:
    assert infer_doc_type(tmp_path / relative, root=tmp_path) == expected


def test_encrypted_pdf_raises_load_error(tmp_path: Path) -> None:
    path = tmp_path / "secret.pdf"
    pdf = pymupdf.open()
    _write_body(pdf.new_page(), 80, FILLER)
    pdf.save(path, encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="pw", owner_pw="owner")
    pdf.close()
    with pytest.raises(PdfLoadError, match="encrypted"):
        load_pdf(path)


def test_corrupted_pdf_raises_load_error(tmp_path: Path) -> None:
    path = tmp_path / "broken.pdf"
    path.write_bytes(b"%PDF-1.4\nthis is not really a pdf")
    with pytest.raises(PdfLoadError):
        load_pdf(path)


# ---------------------------------------------------------------------------- chunker


def test_slugify_and_chunk_id() -> None:
    assert slugify("SOP - Returns and Refunds.pdf") == "sop-returns-and-refunds"
    assert slugify("Product Guide - Lumora Thermostat T2.pdf") == (
        "product-guide-lumora-thermostat-t2"
    )
    assert slugify("???.pdf") == "document"
    assert make_chunk_id("sop-returns", 3, 1) == "sop-returns__p3__c1"


def test_section_for_prefers_preceding_heading() -> None:
    headings = [Heading(0, "1. Overview"), Heading(100, "1.1 Scope")]
    assert section_for(0, 50, headings, None) == "1. Overview"
    assert section_for(150, 50, headings, None) == "1.1 Scope"
    late = [Heading(40, "2. Error Codes")]
    assert section_for(0, 80, late, "1.1 Scope") == "1.1 Scope"
    assert section_for(0, 80, late, None) == "2. Error Codes"
    assert section_for(0, 20, [], None) is None


# --------------------------------------------------------------------------- pipeline


def test_chunks_have_contract_metadata(pdf_dir: Path, small_settings: Settings) -> None:
    chunks = load_and_chunk(pdf_dir, small_settings)
    assert len(chunks) > 3
    for chunk in chunks:
        meta = chunk.metadata
        assert tuple(meta) == CHUNK_METADATA_KEYS
        assert meta["chunk_id"] == make_chunk_id(
            "sop-returns-handbook", meta["page"], meta["chunk_index"]
        )
        assert meta["page"] in {1, 3, 4}
        assert meta["source"] == "SOP - Returns Handbook.pdf"
        assert meta["doc_type"] == "sop"
        assert count_tokens(chunk.page_content) >= MIN_CHUNK_TOKENS
        assert count_tokens(chunk.page_content) <= small_settings.chunk_size_tokens


def test_chunk_ids_unique_and_indexes_contiguous(pdf_dir: Path, small_settings: Settings) -> None:
    chunks = load_and_chunk(pdf_dir, small_settings)
    ids = [c.metadata["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))
    by_page: dict[int, list[int]] = {}
    for chunk in chunks:
        by_page.setdefault(chunk.metadata["page"], []).append(chunk.metadata["chunk_index"])
    for indexes in by_page.values():
        assert indexes == list(range(len(indexes)))
    assert len(by_page[1]) > 1, "page 1 should be split into several chunks"


def test_chunking_is_deterministic(pdf_dir: Path, small_settings: Settings) -> None:
    first = load_and_chunk(pdf_dir, small_settings)
    second = load_and_chunk(pdf_dir, small_settings)
    assert [c.metadata for c in first] == [c.metadata for c in second]
    assert [c.page_content for c in first] == [c.page_content for c in second]


def test_sections_assigned_and_carried_across_pages(
    pdf_dir: Path, small_settings: Settings
) -> None:
    chunks = load_and_chunk(pdf_dir, small_settings)
    sections = {(c.metadata["page"], c.metadata["section"]) for c in chunks}
    assert (1, "1. Overview") in sections
    assert (1, "1.1 Scope") in sections
    assert {s for p, s in sections if p == 3} == {"1.1 Scope"}
    assert {s for p, s in sections if p == 4} == {"2. Error Codes"}


def test_small_fragments_are_dropped(tmp_path: Path, small_settings: Settings) -> None:
    path = tmp_path / "tiny.pdf"
    pdf = pymupdf.open()
    _write_body(pdf.new_page(), 80, "Short note.")
    pdf.save(path)
    pdf.close()
    result = run(tmp_path, small_settings)
    assert result.files == 1
    assert result.pages == 1
    assert result.chunks == []


def test_bad_files_are_skipped_not_fatal(pdf_dir: Path, small_settings: Settings) -> None:
    (pdf_dir / "broken.pdf").write_bytes(b"not a pdf at all")
    secret = pymupdf.open()
    _write_body(secret.new_page(), 80, FILLER)
    secret.save(pdf_dir / "locked.pdf", encryption=pymupdf.PDF_ENCRYPT_AES_256, user_pw="x")
    secret.close()

    result = run(pdf_dir, small_settings)
    assert result.files == 1
    assert sorted(s.source for s in result.skipped) == ["broken.pdf", "locked.pdf"]
    assert {c.metadata["source"] for c in result.chunks} == {"SOP - Returns Handbook.pdf"}


def test_colliding_slugs_are_disambiguated(tmp_path: Path, small_settings: Settings) -> None:
    build_sample_pdf(tmp_path / "Returns Handbook.pdf")
    build_sample_pdf(tmp_path / "Returns_Handbook.pdf")
    chunks = load_and_chunk(tmp_path, small_settings)
    ids = [c.metadata["chunk_id"] for c in chunks]
    assert len(ids) == len(set(ids))
    assert len({cid.split("__")[0] for cid in ids}) == 2


def test_missing_directory_raises(tmp_path: Path, small_settings: Settings) -> None:
    with pytest.raises(FileNotFoundError):
        run(tmp_path / "missing", small_settings)


def test_cli_dry_run_prints_stats(
    pdf_dir: Path, capsys: pytest.CaptureFixture[str], tmp_path: Path
) -> None:
    dump = tmp_path / "chunks.jsonl"
    assert main(["--dry-run", "--pdf-dir", str(pdf_dir), "--dump", str(dump)]) == 0
    out = capsys.readouterr().out
    assert "Files         : 1 processed, 0 skipped" in out
    assert "Pages         : 3" in out
    assert re.search(r"Chunks\s+: \d+", out)
    assert dump.read_text(encoding="utf-8").count("\n") >= 1


def test_cli_without_dry_run_refuses(pdf_dir: Path) -> None:
    assert main(["--pdf-dir", str(pdf_dir)]) == 2


# ---------------------------------------------------------------- sample knowledge base

SAMPLE_DIR = Path(__file__).resolve().parents[1] / "data" / "pdfs"


@pytest.mark.skipif(not any(SAMPLE_DIR.glob("*.pdf")), reason="sample PDFs not generated")
def test_sample_pdfs_chunk_cleanly() -> None:
    """Every embedded fact survives cleaning and lands in a chunk on its own page."""
    from scripts.generate_sample_pdfs import _plain
    from scripts.sample_docs import ALL_DOCS

    settings = Settings(_env_file=None)
    chunks = load_and_chunk(SAMPLE_DIR, settings)
    assert {c.metadata["source"] for c in chunks} == {d.filename for d in ALL_DOCS}

    def norm(text: str) -> str:
        return re.sub(r"\s+", " ", text).strip()

    by_page: dict[tuple[str, int], list[str]] = {}
    for chunk in chunks:
        key = (chunk.metadata["source"], chunk.metadata["page"])
        by_page.setdefault(key, []).append(norm(chunk.page_content))
        assert "Internal use only" not in chunk.page_content
        assert not re.search(r"Page \d+ of \d+", chunk.page_content)
        assert chunk.metadata["section"]

    for doc in ALL_DOCS:
        with pymupdf.open(SAMPLE_DIR / doc.filename) as pdf:
            page_texts = [norm(page.get_text()) for page in pdf]
        for fct in doc.facts:
            for needle in fct.needles:
                target = norm(_plain(needle))
                page = next(i + 1 for i, text in enumerate(page_texts) if target in text)
                assert any(target in text for text in by_page.get((doc.filename, page), [])), (
                    f"{fct.id}: {target!r} not found in chunks of {doc.filename} p.{page}"
                )
