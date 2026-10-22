"""Tests for the sample PDF generator (scripts/generate_sample_pdfs.py)."""

import hashlib
import re
from pathlib import Path

import pymupdf
import pytest

from scripts.generate_sample_pdfs import FACTS_FILENAME, FactLocationError, generate, locate_facts
from scripts.sample_docs import ALL_DOCS
from scripts.sample_docs.model import SampleDoc, fact, p


@pytest.fixture(scope="module")
def generated(tmp_path_factory: pytest.TempPathFactory):
    out_dir = tmp_path_factory.mktemp("pdfs")
    located, page_counts = generate(out_dir)
    return out_dir, located, page_counts


def _digest(directory: Path) -> dict[str, str]:
    return {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(directory.iterdir())
    }


def test_generates_expected_document_set(generated) -> None:
    out_dir, _, page_counts = generated
    pdfs = sorted(path.name for path in out_dir.glob("*.pdf"))
    assert pdfs == sorted(doc.filename for doc in ALL_DOCS)
    assert len(pdfs) == 12
    assert 60 <= sum(page_counts.values()) <= 80

    types = [doc.doc_type for doc in ALL_DOCS]
    assert types.count("product_guide") == 4
    assert types.count("sop") == 4
    assert types.count("faq") == 3
    assert types.count("policy") == 1


def test_pdfs_have_title_metadata_and_page_footers(generated) -> None:
    out_dir, _, _ = generated
    for doc in ALL_DOCS:
        with pymupdf.open(out_dir / doc.filename) as pdf:
            assert pdf.metadata["title"] == doc.title
            total = pdf.page_count
            for number, page in enumerate(pdf, start=1):
                assert f"Page {number} of {total}" in page.get_text()


def test_facts_cover_requirements(generated) -> None:
    _, located, _ = generated
    assert len(located) >= 40
    kinds = [item.fact.kind for item in located]
    assert kinds.count("cross-page") >= 3
    assert kinds.count("table") >= 3
    assert sum("confusable" in item.fact.tags for item in located) >= 2
    assert len({item.fact.id for item in located}) == len(located)
    for item in located:
        if item.fact.kind == "cross-page":
            assert len(item.pages) == 2 and item.pages[1] == item.pages[0] + 1


def test_facts_markdown_lists_every_fact_with_file_and_page(generated) -> None:
    out_dir, located, _ = generated
    text = (out_dir / FACTS_FILENAME).read_text(encoding="utf-8")
    rows = [line for line in text.splitlines() if re.match(r"^\| [A-Z0-9]+(-[A-Z0-9]+)+ \|", line)]
    assert len(rows) == len(located)
    for item in located:
        pages = "-".join(str(n) for n in item.pages)
        assert f"| {item.fact.id} |" in text
        assert f"| {item.doc.filename} | {pages} |" in text


def test_fact_pages_match_pdf_text(generated) -> None:
    """Independently re-check a sample of facts against the raw page text."""
    out_dir, located, _ = generated
    for item in located[::7]:
        with pymupdf.open(out_dir / item.doc.filename) as pdf:
            first_page = " ".join(pdf[item.pages[0] - 1].get_text().split())
        assert " ".join(item.fact.needles[0].split()) in first_page


def test_output_is_deterministic(generated, tmp_path: Path) -> None:
    out_dir, _, _ = generated
    generate(tmp_path)
    assert _digest(tmp_path) == _digest(out_dir)


def test_missing_needle_fails_loudly(tmp_path: Path) -> None:
    from scripts.generate_sample_pdfs import render_pdf

    doc = SampleDoc(
        filename="probe.pdf",
        title="Probe",
        doc_type="faq",
        doc_number="X-1",
        revision="1",
        effective_date="today",
        owner="QA",
        audience="QA",
        purpose="Probe document.",
        blocks=(p("Only this sentence exists."),),
        facts=(fact("X-01", "Missing", "this text is not in the document"),),
    )
    render_pdf(doc, tmp_path / doc.filename)
    with pytest.raises(FactLocationError):
        locate_facts(doc, tmp_path / doc.filename)
