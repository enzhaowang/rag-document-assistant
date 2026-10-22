"""Chroma vector store factory.

`get_vectorstore()` returns a `langchain_chroma.Chroma` bound to the configured collection.
The Chroma client depends on CHROMA_MODE:

- ``local``: an embedded `chromadb.PersistentClient` writing to CHROMA_PERSIST_DIR;
- ``http``:  a `chromadb.HttpClient` talking to a Chroma server at CHROMA_HOST:CHROMA_PORT.

Collections are created with cosine distance. Chroma reports cosine *distance*
(``1 - cosine_similarity``, range 0-2, lower is closer); `app.retrieval.retriever` converts
it to a 0-1 similarity. An existing collection that uses another metric is rejected,
because its scores would not mean what the retrieval threshold expects.
"""

from __future__ import annotations

import logging

import chromadb
from chromadb.config import Settings as ChromaClientSettings
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_openai import OpenAIEmbeddings

from app.config import Settings, get_settings

logger = logging.getLogger(__name__)

DISTANCE_METRIC = "cosine"


class VectorStoreConfigError(RuntimeError):
    """Raised when the vector store collection is not configured as this app expects."""


def get_embeddings(settings: Settings | None = None) -> OpenAIEmbeddings:
    """Create the embeddings client from Settings (endpoint and key passed explicitly)."""
    s = settings or get_settings()
    return OpenAIEmbeddings(
        model=s.openai_embedding_model,
        base_url=s.embedding_base_url,
        api_key=s.require_embedding_api_key(),
        # Chunks are ~500 tokens, so no client-side pre-splitting is needed; sending raw
        # text (not tiktoken IDs) also keeps OpenAI-compatible endpoints such as
        # OpenRouter working.
        check_embedding_ctx_length=False,
    )


def get_chroma_client(settings: Settings | None = None) -> chromadb.ClientAPI:
    """Create a Chroma client for CHROMA_MODE ("local" or "http")."""
    s = settings or get_settings()
    client_settings = ChromaClientSettings(anonymized_telemetry=False)
    if s.chroma_mode == "http":
        logger.debug(
            "connecting to chroma server", extra={"host": s.chroma_host, "port": s.chroma_port}
        )
        return chromadb.HttpClient(host=s.chroma_host, port=s.chroma_port, settings=client_settings)
    s.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    logger.debug("opening local chroma store", extra={"path": str(s.chroma_persist_dir)})
    return chromadb.PersistentClient(path=str(s.chroma_persist_dir), settings=client_settings)


def collection_distance_metric(store: Chroma) -> str | None:
    """Return the distance metric ("cosine", "l2", "ip") of the store's collection."""
    configuration = store._collection.configuration or {}
    for index in ("hnsw", "spann"):
        space = (configuration.get(index) or {}).get("space")
        if space:
            return str(space)
    return None


def ensure_cosine(store: Chroma) -> None:
    """Raise VectorStoreConfigError unless the collection uses cosine distance."""
    metric = collection_distance_metric(store)
    if metric != DISTANCE_METRIC:
        raise VectorStoreConfigError(
            f"Chroma collection {store._collection.name!r} uses distance metric {metric!r}, "
            f"expected {DISTANCE_METRIC!r}. Re-create it with: "
            "python -m app.ingestion.pipeline --reset"
        )


def get_vectorstore(
    settings: Settings | None = None,
    *,
    embeddings: Embeddings | None = None,
    client: chromadb.ClientAPI | None = None,
) -> Chroma:
    """Return the LangChain Chroma store for CHROMA_COLLECTION (created if missing).

    `embeddings` and `client` can be injected (tests, app lifespan); by default they are
    built from Settings. The collection is checked to use cosine distance.
    """
    s = settings or get_settings()
    store = Chroma(
        collection_name=s.chroma_collection,
        embedding_function=embeddings if embeddings is not None else get_embeddings(s),
        client=client if client is not None else get_chroma_client(s),
        collection_configuration={"hnsw": {"space": DISTANCE_METRIC}},
    )
    ensure_cosine(store)
    return store
