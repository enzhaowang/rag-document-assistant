"""Vector store, idempotent ingestion and scored retrieval (embeddings are faked)."""

from __future__ import annotations

import math
import re
from pathlib import Path
from typing import Any

import pymupdf
import pytest
from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings

from app.config import MissingOpenAIKeyError, Settings
from app.ingestion import pipeline
from app.ingestion.pipeline import call_with_retry, doc_slug_of, ingest, main
from app.retrieval import vectorstore as vectorstore_module
from app.retrieval.retriever import (
    RetrievedChunk,
    distance_to_similarity,
    filter_by_threshold,
    retrieve,
)
from app.retrieval.vectorstore import (
    VectorStoreConfigError,
    collection_distance_metric,
    ensure_cosine,
    get_chroma_client,
    get_embeddings,
    get_vectorstore,
)

VOCAB = ("refund", "warranty", "shipping", "thermostat", "error", "password", "battery", "sensor")
_WORD = re.compile(r"[a-z]+")


class KeywordEmbeddings(Embeddings):
    """Deterministic bag-of-keywords embeddings that record every embedded text."""

    def __init__(self, fail_times: int = 0, error: Exception | None = None) -> None:
        self.embedded: list[str] = []
        self.calls = 0
        self._fail_times = fail_times
        self._error = error or ConnectionError("temporary network failure")

    def _vector(self, text: str) -> list[float]:
        words = _WORD.findall(text.lower())
        counts = [float(sum(w.startswith(term) for w in words)) for term in VOCAB]
        return [*counts, 0.05]  # constant component keeps the vector non-zero

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        self.calls += 1
        if self.calls <= self._fail_times:
            raise self._error
        self.embedded.extend(texts)
        return [self._vector(t) for t in texts]

    def embed_query(self, text: str) -> list[float]:
        return self._vector(text)


def _paragraph(topic: str, sentences: int = 6) -> str:
    sentence = (
        f"The {topic} team documents every {topic} case with the order number, the "
        f"customer name and the agreed {topic} outcome before closing the ticket. "
    )
    return sentence * sentences


def write_pdf(path: Path, pages: list[str], title: str) -> Path:
    pdf = pymupdf.open()
    for text in pages:
        page = pdf.new_page(width=612, height=792)
        assert page.insert_textbox(pymupdf.Rect(72, 72, 540, 720), text, fontsize=10) >= 0
    pdf.set_metadata({"title": title})
    pdf.save(path)
    pdf.close()
    return path


@pytest.fixture
def settings(tmp_path: Path) -> Settings:
    return Settings(
        _env_file=None,
        chroma_mode="local",
        chroma_persist_dir=tmp_path / "chroma",
        chroma_collection="test_docs",
        pdf_dir=tmp_path / "pdfs",
        chunk_size_tokens=80,
        chunk_overlap_tokens=10,
        retrieval_top_k=3,
        retrieval_score_threshold=0.5,
    )


@pytest.fixture
def pdf_dir(settings: Settings) -> Path:
    directory = settings.pdf_dir
    directory.mkdir()
    write_pdf(
        directory / "SOP - Refunds.pdf",
        [_paragraph("refund"), _paragraph("refund", 3) + _paragraph("shipping", 3)],
        "Refunds SOP",
    )
    write_pdf(directory / "FAQ - Passwords.pdf", [_paragraph("password")], "Password FAQ")
    write_pdf(
        directory / "Product Guide - Thermostat.pdf",
        [_paragraph("thermostat"), _paragraph("battery"), _paragraph("error")],
        "Thermostat Guide",
    )
    return directory


@pytest.fixture
def embeddings() -> KeywordEmbeddings:
    return KeywordEmbeddings()


@pytest.fixture
def store(settings: Settings, embeddings: KeywordEmbeddings):
    return get_vectorstore(settings, embeddings=embeddings)


def _ids(store) -> set[str]:
    return set(store.get(include=[])["ids"])


def _no_sleep(_: float) -> None:
    return None


# ------------------------------------------------------------------------ vector store


def test_vectorstore_collection_uses_cosine(store) -> None:
    assert collection_distance_metric(store) == "cosine"
    ensure_cosine(store)  # does not raise


def test_existing_non_cosine_collection_is_rejected(settings: Settings) -> None:
    client = get_chroma_client(settings)
    client.create_collection(settings.chroma_collection, configuration={"hnsw": {"space": "l2"}})
    with pytest.raises(VectorStoreConfigError, match="--reset"):
        get_vectorstore(settings, embeddings=KeywordEmbeddings(), client=client)


def test_local_mode_persists_to_configured_dir(settings: Settings, embeddings) -> None:
    first = get_vectorstore(settings, embeddings=embeddings)
    first.add_texts(["refund policy"], metadatas=[{"chunk_id": "a__p1__c0"}], ids=["a__p1__c0"])
    assert settings.chroma_persist_dir.is_dir()
    reopened = get_vectorstore(settings, embeddings=embeddings)
    assert _ids(reopened) == {"a__p1__c0"}


def test_http_mode_uses_http_client(settings: Settings, monkeypatch: pytest.MonkeyPatch) -> None:
    captured: dict[str, Any] = {}

    def fake_http_client(**kwargs: Any) -> str:
        captured.update(kwargs)
        return "http-client"

    monkeypatch.setattr(vectorstore_module.chromadb, "HttpClient", fake_http_client)
    http_settings = settings.model_copy(
        update={"chroma_mode": "http", "chroma_host": "chroma.internal", "chroma_port": 9000}
    )
    assert get_chroma_client(http_settings) == "http-client"
    assert captured["host"] == "chroma.internal"
    assert captured["port"] == 9000


def test_embeddings_client_uses_settings_endpoint_and_key() -> None:
    s = Settings(
        _env_file=None,
        openai_api_key="sk-test-key",
        openai_base_url="https://openrouter.example/api/v1",
        openai_embedding_model="openai/text-embedding-3-small",
    )
    client = get_embeddings(s)
    assert client.model == "openai/text-embedding-3-small"
    assert client.openai_api_base == "https://openrouter.example/api/v1"
    assert client.openai_api_key.get_secret_value() == "sk-test-key"
    assert client.check_embedding_ctx_length is False


def test_embeddings_client_requires_key() -> None:
    with pytest.raises(MissingOpenAIKeyError):
        get_embeddings(Settings(_env_file=None, openai_api_key=None))


# --------------------------------------------------------------------------- ingestion


def test_first_ingest_writes_every_chunk(pdf_dir: Path, settings: Settings, store, embeddings):
    result, stats = ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)
    chunk_ids = {c.metadata["chunk_id"] for c in result.chunks}
    assert len(chunk_ids) == len(result.chunks) > 3
    assert stats.files_new == 3
    assert stats.chunks_added == len(result.chunks)
    assert stats.chunks_total == len(result.chunks)
    assert _ids(store) == chunk_ids
    assert len(embeddings.embedded) == len(result.chunks)


def test_second_ingest_is_a_no_op(pdf_dir: Path, settings: Settings, store, embeddings) -> None:
    first, _ = ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)
    embedded_before = len(embeddings.embedded)

    _, stats = ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)

    assert stats.chunks_added == 0
    assert stats.chunks_deleted == 0
    assert stats.files_unchanged == 3
    assert stats.chunks_total == len(first.chunks)
    assert len(embeddings.embedded) == embedded_before  # nothing re-embedded


def test_repeated_upsert_never_duplicates(pdf_dir: Path, settings: Settings, store) -> None:
    result, _ = ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)
    # Force re-writing the same chunk_ids: the store must still hold one vector per id.
    pipeline._upsert(store, result.chunks, batch_size=7, sleep=_no_sleep)
    assert store._collection.count() == len(result.chunks)


def test_changed_file_replaces_its_chunks(pdf_dir: Path, settings: Settings, store) -> None:
    ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)
    slug = "product-guide-thermostat"
    before = {i for i in _ids(store) if doc_slug_of(i) == slug}
    other_before = _ids(store) - before

    write_pdf(pdf_dir / "Product Guide - Thermostat.pdf", [_paragraph("sensor")], "Thermostat")
    result, stats = ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)

    after = {i for i in _ids(store) if doc_slug_of(i) == slug}
    expected = {
        c.metadata["chunk_id"] for c in result.chunks if doc_slug_of(c.metadata["chunk_id"]) == slug
    }
    assert stats.files_changed == 1
    assert stats.files_unchanged == 2
    assert after == expected
    assert len(before - after) == stats.chunks_deleted > 0
    assert _ids(store) - after == other_before
    stored = store.get(ids=sorted(after), include=["metadatas", "documents"])
    hashes = {m["doc_hash"] for m in stored["metadatas"]}
    assert len(hashes) == 1
    assert all("sensor" in text for text in stored["documents"])


def test_deleted_file_is_removed_from_index(pdf_dir: Path, settings: Settings, store) -> None:
    ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)
    (pdf_dir / "FAQ - Passwords.pdf").unlink()

    _, stats = ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)

    assert stats.files_removed == 1
    assert stats.chunks_deleted > 0
    assert not any(doc_slug_of(i) == "faq-passwords" for i in _ids(store))


def test_unreadable_file_keeps_existing_chunks(pdf_dir: Path, settings: Settings, store) -> None:
    ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)
    before = _ids(store)
    (pdf_dir / "FAQ - Passwords.pdf").write_bytes(b"%PDF-1.7 corrupted")

    result, stats = ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)

    assert [s.source for s in result.skipped] == ["FAQ - Passwords.pdf"]
    assert stats.files_removed == 0
    assert _ids(store) == before


def test_reset_rebuilds_collection(pdf_dir: Path, settings: Settings, store, embeddings) -> None:
    first, _ = ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)
    store.add_texts(["orphan"], metadatas=[{"doc_hash": "x"}], ids=["ghost__p1__c0"])

    _, stats = ingest(pdf_dir, settings, vectorstore=store, reset=True, sleep=_no_sleep)

    assert stats.reset is True
    assert stats.files_new == 3
    assert stats.chunks_added == len(first.chunks)
    assert "ghost__p1__c0" not in _ids(store)
    assert collection_distance_metric(store) == "cosine"


def test_ingest_writes_in_batches(pdf_dir: Path, settings: Settings, store, embeddings) -> None:
    result, _ = ingest(pdf_dir, settings, vectorstore=store, batch_size=2, sleep=_no_sleep)
    per_doc: dict[str, int] = {}
    for chunk in result.chunks:
        slug = doc_slug_of(chunk.metadata["chunk_id"])
        per_doc[slug] = per_doc.get(slug, 0) + 1
    assert embeddings.calls == sum(math.ceil(n / 2) for n in per_doc.values())


def test_ingest_retries_transient_failures(pdf_dir: Path, settings: Settings) -> None:
    flaky = KeywordEmbeddings(fail_times=2)
    store = get_vectorstore(settings, embeddings=flaky)
    delays: list[float] = []

    result, stats = ingest(pdf_dir, settings, vectorstore=store, sleep=delays.append)

    assert delays == [1.0, 2.0]  # exponential backoff
    assert stats.chunks_added == len(result.chunks)
    assert store._collection.count() == len(result.chunks)


def test_retry_gives_up_after_max_attempts() -> None:
    delays: list[float] = []

    def always_fails() -> None:
        raise TimeoutError("still down")

    with pytest.raises(TimeoutError):
        call_with_retry(always_fails, what="test", attempts=4, sleep=delays.append)
    assert delays == [1.0, 2.0, 4.0]


def test_retry_does_not_retry_auth_errors() -> None:
    class AuthError(Exception):
        status_code = 401

    calls = 0

    def unauthorized() -> None:
        nonlocal calls
        calls += 1
        raise AuthError("invalid api key")

    with pytest.raises(AuthError):
        call_with_retry(unauthorized, what="test", sleep=_no_sleep)
    assert calls == 1


def test_none_metadata_round_trips(settings: Settings, store) -> None:
    chunk = Document(
        page_content="Refund requests are reviewed by the refund desk within two days.",
        metadata={
            "chunk_id": "doc__p1__c0",
            "source": "doc.pdf",
            "doc_title": "Doc",
            "doc_type": "sop",
            "page": 1,
            "chunk_index": 0,
            "doc_hash": "abc",
            "section": None,
        },
    )
    pipeline._upsert(store, [chunk], batch_size=10, sleep=_no_sleep)
    [hit] = retrieve("refund", k=1, vectorstore=store, settings=settings)
    assert hit.metadata == chunk.metadata


def test_ingest_rejects_bad_batch_size(pdf_dir: Path, settings: Settings, store) -> None:
    with pytest.raises(ValueError):
        ingest(pdf_dir, settings, vectorstore=store, batch_size=0)


# --------------------------------------------------------------------------- retrieval


@pytest.mark.parametrize(
    ("distance", "similarity"),
    [(0.0, 1.0), (0.25, 0.75), (1.0, 0.0), (1.6, 0.0), (2.0, 0.0), (-1e-7, 1.0)],
)
def test_distance_to_similarity(distance: float, similarity: float) -> None:
    assert distance_to_similarity(distance) == pytest.approx(similarity)


def test_retrieve_scores_are_similarities(pdf_dir: Path, settings: Settings, store) -> None:
    ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)

    results = retrieve("password reset rules", vectorstore=store, settings=settings)

    assert len(results) == settings.retrieval_top_k
    assert all(isinstance(r, RetrievedChunk) for r in results)
    assert all(0.0 <= r.score <= 1.0 for r in results)
    scores = [r.score for r in results]
    assert scores == sorted(scores, reverse=True)  # best first
    assert results[0].metadata["source"] == "FAQ - Passwords.pdf"
    assert results[0].score > 0.9  # near-identical direction -> similarity close to 1
    assert results[-1].score < 0.5  # unrelated chunk -> low similarity, not high distance
    assert results[0].chunk_id == results[0].metadata["chunk_id"]


def test_retrieve_matches_chroma_distance(pdf_dir: Path, settings: Settings, store) -> None:
    ingest(pdf_dir, settings, vectorstore=store, sleep=_no_sleep)
    raw = store.similarity_search_with_score("battery life", k=2)
    results = retrieve("battery life", k=2, vectorstore=store, settings=settings)
    for (doc, distance), chunk in zip(raw, results, strict=True):
        assert chunk.chunk_id == doc.metadata["chunk_id"]
        assert chunk.score == pytest.approx(1.0 - distance)


def test_retrieve_validates_input(settings: Settings, store) -> None:
    with pytest.raises(ValueError):
        retrieve("   ", vectorstore=store, settings=settings)
    with pytest.raises(ValueError):
        retrieve("refund", k=0, vectorstore=store, settings=settings)


def test_retrieve_on_empty_store_returns_nothing(settings: Settings, store) -> None:
    assert retrieve("refund", vectorstore=store, settings=settings) == []


def _chunk(score: float) -> RetrievedChunk:
    return RetrievedChunk(doc=Document(page_content="x", metadata={"chunk_id": "c"}), score=score)


def test_filter_by_threshold_keeps_scores_at_or_above_limit() -> None:
    chunks = [_chunk(0.9), _chunk(0.5), _chunk(0.49), _chunk(0.1)]
    assert [c.score for c in filter_by_threshold(chunks, 0.5)] == [0.9, 0.5]
    assert filter_by_threshold(chunks, 0.95) == []


def test_filter_by_threshold_defaults_to_settings(clean_env: Path) -> None:
    (clean_env / ".env").write_text("RETRIEVAL_SCORE_THRESHOLD=0.6\n", encoding="utf-8")
    assert [c.score for c in filter_by_threshold([_chunk(0.7), _chunk(0.55)])] == [0.7]


# --------------------------------------------------------------------------------- CLI


def test_cli_indexes_and_prints_stats(
    pdf_dir: Path,
    settings: Settings,
    store,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.setattr(pipeline, "get_settings", lambda: settings)
    monkeypatch.setattr(pipeline, "get_vectorstore", lambda s: store)

    assert main(["--pdf-dir", str(pdf_dir)]) == 0
    assert "Documents     : 3 new" in capsys.readouterr().out

    assert main(["--pdf-dir", str(pdf_dir)]) == 0
    out = capsys.readouterr().out
    assert "New chunks    : 0" in out
    assert "3 unchanged" in out

    assert main(["--pdf-dir", str(pdf_dir), "--reset"]) == 0
    assert "Reset         : collection dropped and re-created" in capsys.readouterr().out


def test_cli_reports_missing_key(
    pdf_dir: Path, settings: Settings, monkeypatch: pytest.MonkeyPatch
) -> None:
    keyless = settings.model_copy(update={"openai_api_key": None})
    monkeypatch.setattr(pipeline, "get_settings", lambda: keyless)
    assert main(["--pdf-dir", str(pdf_dir)]) == 1


def test_cli_rejects_reset_with_dry_run(pdf_dir: Path) -> None:
    with pytest.raises(SystemExit) as excinfo:
        main(["--dry-run", "--reset", "--pdf-dir", str(pdf_dir)])
    assert excinfo.value.code == 2


# ------------------------------------------------------------------- check_retrieval.py


def test_check_retrieval_questions_reference_real_facts() -> None:
    from scripts.check_retrieval import QUESTIONS, parse_facts

    facts_path = Path(__file__).resolve().parents[1] / "data" / "pdfs" / "FACTS.md"
    if not facts_path.exists():
        pytest.skip("FACTS.md not generated")
    facts = parse_facts(facts_path)
    assert len(QUESTIONS) == 10
    for fact_id, _ in QUESTIONS:
        assert fact_id in facts
        assert facts[fact_id].source.endswith(".pdf")
        assert facts[fact_id].pages
    assert facts["PG-T3-05"].pages == {3, 4}  # cross-page range is expanded
