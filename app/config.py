"""Application settings loaded from environment variables and an optional `.env` file.

Every tunable value (model names, paths, chunking and retrieval parameters, endpoints)
lives here. Other modules must read configuration through `get_settings()` instead of
hard-coding values.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class MissingOpenAIKeyError(RuntimeError):
    """Raised when a code path needs OpenAI but OPENAI_API_KEY is not configured."""


class Settings(BaseSettings):
    """Typed application configuration.

    Field names map case-insensitively to environment variables, e.g. `chunk_size_tokens`
    is read from `CHUNK_SIZE_TOKENS`. Values from the real environment take precedence
    over values in `.env`.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # OpenAI. The key is optional at load time so that tooling which does not call
    # OpenAI (lint, unit tests, PDF generation, chunking) works without it.
    # Any OpenAI-compatible endpoint works via OPENAI_BASE_URL, e.g. OpenRouter
    # (https://openrouter.ai/api/v1, with model names such as "openai/gpt-4o-mini").
    openai_api_key: SecretStr | None = None
    openai_base_url: str = Field(default="https://api.openai.com/v1", min_length=1)
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"
    # Optional overrides for embeddings only; blank means "same as the chat endpoint".
    openai_embedding_base_url: str | None = None
    openai_embedding_api_key: SecretStr | None = None

    # Vector store
    chroma_mode: Literal["local", "http"] = "local"
    chroma_persist_dir: Path = Path("./.chroma")
    chroma_host: str = "chroma"
    chroma_port: int = Field(default=8000, ge=1, le=65535)
    chroma_collection: str = Field(default="company_docs", min_length=1)

    # Ingestion
    pdf_dir: Path = Path("./data/pdfs")
    chunk_size_tokens: int = Field(default=500, gt=0)
    chunk_overlap_tokens: int = Field(default=80, ge=0)

    # Retrieval
    retrieval_top_k: int = Field(default=6, gt=0)
    retrieval_score_threshold: float = Field(default=0.35, ge=0.0, le=1.0)

    # LLM calls (chat model): per-request timeout and SDK-level retries with backoff.
    openai_timeout_seconds: float = Field(default=30.0, gt=0)
    openai_max_retries: int = Field(default=2, ge=0)

    # RAG chain: token budget for retrieved context sent to the LLM, and how many recent
    # conversation turns (one user + one assistant message each) are kept as history.
    rag_max_context_tokens: int = Field(default=3000, gt=0)
    rag_history_max_turns: int = Field(default=6, ge=0)

    # UI -> API. The Streamlit UI reads these (and RAG_HISTORY_MAX_TURNS) with its own
    # small settings class so that it never imports backend code; keep defaults in sync.
    api_base_url: str = "http://localhost:8080"
    ui_request_timeout_seconds: float = Field(default=120.0, gt=0)

    # HTTP API. API_CORS_ORIGINS is a comma-separated list of allowed browser origins
    # ("*" allows any origin). ADMIN_API_KEY protects POST /ingest; blank disables it.
    api_cors_origins: str = "http://localhost:8501"
    admin_api_key: SecretStr | None = None

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

    @field_validator(
        "openai_embedding_base_url", "openai_embedding_api_key", "admin_api_key", mode="before"
    )
    @classmethod
    def _blank_to_none(cls, value: object) -> object:
        if isinstance(value, str) and not value.strip():
            return None
        return value

    @model_validator(mode="after")
    def _check_chunk_overlap(self) -> "Settings":
        if self.chunk_overlap_tokens >= self.chunk_size_tokens:
            raise ValueError(
                "CHUNK_OVERLAP_TOKENS must be smaller than CHUNK_SIZE_TOKENS "
                f"(got {self.chunk_overlap_tokens} >= {self.chunk_size_tokens})"
            )
        return self

    def require_openai_api_key(self) -> str:
        """Return the OpenAI API key, or raise a clear error if it is not configured.

        Call this right before constructing any OpenAI client.
        """
        key = self.openai_api_key.get_secret_value().strip() if self.openai_api_key else ""
        if not key:
            raise MissingOpenAIKeyError(
                "OPENAI_API_KEY is not set. Copy .env.example to .env and add your key, "
                "or export OPENAI_API_KEY in your shell."
            )
        return key

    @property
    def cors_origins(self) -> list[str]:
        """API_CORS_ORIGINS split into a list of origins (blank entries removed)."""
        return [origin.strip() for origin in self.api_cors_origins.split(",") if origin.strip()]

    @property
    def embedding_base_url(self) -> str:
        """Base URL for the embeddings endpoint (falls back to OPENAI_BASE_URL)."""
        return self.openai_embedding_base_url or self.openai_base_url

    def require_embedding_api_key(self) -> str:
        """Return the embeddings API key (falls back to OPENAI_API_KEY).

        Call this right before constructing any embeddings client.
        """
        if self.openai_embedding_api_key:
            key = self.openai_embedding_api_key.get_secret_value().strip()
            if key:
                return key
        return self.require_openai_api_key()


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide Settings instance (cached after the first call)."""
    return Settings()
