"""Application settings loaded from environment variables and an optional `.env` file.

Every tunable value (model names, paths, chunking and retrieval parameters, endpoints)
lives here. Other modules must read configuration through `get_settings()` instead of
hard-coding values.
"""

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field, SecretStr, model_validator
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
    openai_api_key: SecretStr | None = None
    openai_chat_model: str = "gpt-4o-mini"
    openai_embedding_model: str = "text-embedding-3-small"

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

    # UI -> API
    api_base_url: str = "http://localhost:8080"

    # Logging
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"

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


@lru_cache
def get_settings() -> Settings:
    """Return the process-wide Settings instance (cached after the first call)."""
    return Settings()
