"""Long-lived backend resources shared by all API requests.

`RagService` owns the Chroma client, the LangChain vector store and the chat model. They
are created once (at startup by the app lifespan, or lazily on first use if startup
initialization failed, e.g. because Chroma was not up yet) and then reused by every
request. All methods are blocking and must be called from a worker thread, never directly
inside an `async def` endpoint.
"""

from __future__ import annotations

import logging
import threading
from collections.abc import Sequence
from datetime import UTC, datetime

import chromadb
from chromadb.errors import NotFoundError
from langchain_chroma import Chroma
from langchain_core.language_models import BaseChatModel

from app.config import Settings
from app.ingestion.pipeline import ingest
from app.rag.chain import answer_question, build_chat_model
from app.rag.schemas import ChatResult, HistoryMessage
from app.retrieval.vectorstore import get_chroma_client, get_vectorstore

logger = logging.getLogger(__name__)

# Page size when reading metadata to count distinct documents.
_READ_PAGE_SIZE = 1000


class BackendUnavailableError(RuntimeError):
    """Raised when the vector store (Chroma) cannot be reached or its client cannot be created.

    chromadb does not raise a consistent exception type here: `chromadb.HttpClient`
    contacts the server while it is being constructed and turns transport failures into a
    plain `ValueError` ("Could not connect to a Chroma server..." or "Server disconnected
    without sending a response."). Wrapping every client-creation failure in this type lets
    the API map it to a 503 without treating unrelated `ValueError`s as outages.
    """


class RagService:
    """Lazily created, cached clients plus the operations the API exposes."""

    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self._init_lock = threading.Lock()
        self._ingest_lock = threading.Lock()
        self._client: chromadb.ClientAPI | None = None
        self._vectorstore: Chroma | None = None
        self._llm: BaseChatModel | None = None
        # (chunk_count, document_count) from the last metadata scan.
        self._document_count_cache: tuple[int, int] | None = None

    # ------------------------------------------------------------------ resources

    def client(self) -> chromadb.ClientAPI:
        with self._init_lock:
            if self._client is None:
                try:
                    self._client = get_chroma_client(self.settings)
                except Exception as exc:
                    raise BackendUnavailableError(
                        f"could not create the Chroma client ({type(exc).__name__}: {exc})"
                    ) from exc
            return self._client

    def vectorstore(self) -> Chroma:
        client = self.client()
        with self._init_lock:
            if self._vectorstore is None:
                self._vectorstore = get_vectorstore(self.settings, client=client)
            return self._vectorstore

    def llm(self) -> BaseChatModel:
        with self._init_lock:
            if self._llm is None:
                self._llm = build_chat_model(self.settings)
            return self._llm

    def warm_up(self) -> None:
        """Create all clients now. Failures are logged; creation is retried on first use."""
        try:
            self.vectorstore()
            self.llm()
        except Exception as exc:  # noqa: BLE001 - startup must not crash the API
            logger.warning(
                "backend initialization failed; will retry on the next request",
                extra={"error_type": type(exc).__name__},
            )
        else:
            logger.info(
                "backend initialized",
                extra={
                    "chroma_mode": self.settings.chroma_mode,
                    "collection": self.settings.chroma_collection,
                    "chat_model": self.settings.openai_chat_model,
                },
            )

    # ------------------------------------------------------------------ operations

    def answer(self, question: str, history: Sequence[HistoryMessage]) -> ChatResult:
        """Run the RAG chain with the shared vector store and chat model."""
        return answer_question(
            question,
            history,
            settings=self.settings,
            llm=self.llm(),
            vectorstore=self.vectorstore(),
        )

    def index_counts(self) -> tuple[int, int]:
        """Return (chunk_count, document_count) of the collection; (0, 0) if it is missing.

        Talks to Chroma directly (no embeddings client), so it works without an OpenAI key.
        """
        try:
            collection = self.client().get_collection(self.settings.chroma_collection)
        except NotFoundError:
            return 0, 0
        chunk_count = collection.count()
        cached = self._document_count_cache
        if cached is not None and cached[0] == chunk_count:
            return cached
        documents: set[str] = set()
        offset = 0
        while True:
            page = collection.get(include=["metadatas"], limit=_READ_PAGE_SIZE, offset=offset)
            for metadata in page["metadatas"] or []:
                source = (metadata or {}).get("source")
                if source:
                    documents.add(str(source))
            if len(page["ids"]) < _READ_PAGE_SIZE:
                break
            offset += len(page["ids"])
        self._document_count_cache = (chunk_count, len(documents))
        return self._document_count_cache

    def try_start_ingest(self) -> bool:
        """Reserve the ingestion slot; False if a run is already in progress."""
        return self._ingest_lock.acquire(blocking=False)

    def run_ingest(self) -> None:
        """Incrementally re-ingest PDF_DIR. Releases the slot taken by `try_start_ingest`."""
        started = datetime.now(UTC)
        try:
            _, stats = ingest(settings=self.settings, vectorstore=self.vectorstore())
        except Exception:
            logger.exception("background ingestion failed")
        else:
            logger.info(
                "background ingestion finished",
                extra={
                    "files_new": stats.files_new,
                    "files_changed": stats.files_changed,
                    "files_unchanged": stats.files_unchanged,
                    "files_removed": stats.files_removed,
                    "chunks_added": stats.chunks_added,
                    "chunks_deleted": stats.chunks_deleted,
                    "chunks_total": stats.chunks_total,
                    "duration_s": round((datetime.now(UTC) - started).total_seconds(), 2),
                },
            )
        finally:
            # The set of documents may have changed even if the chunk total did not.
            self._document_count_cache = None
            self._ingest_lock.release()
