"""Request and response models for the HTTP API.

`ChatRequest` / `ChatResponse` implement the `/chat` contract:

- request: ``{"question": str (1-2000 chars), "history": [{"role", "content"}]}``;
  `history` is optional and only its last RAG_HISTORY_MAX_TURNS turns (Settings, default
  6) are used;
- response: ``{"answer", "is_answerable", "sources": [...], "model", "latency_ms"}``.

These models are deliberately separate from the chain's `ChatResult`, which carries extra
diagnostic fields that are not part of the public contract.
"""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.rag.schemas import ChatResult

QUESTION_MAX_CHARS = 2000
# How many recent turns are kept is configured by Settings.rag_history_max_turns
# (RAG_HISTORY_MAX_TURNS) and applied by `recent_history`, so the API and the chain agree.
# Hard limits that reject abusive payloads instead of silently truncating them.
HISTORY_MAX_MESSAGES = 50
HISTORY_MESSAGE_MAX_CHARS = 8000


class ChatMessage(BaseModel):
    """One previous message of the conversation, oldest first."""

    model_config = ConfigDict(extra="forbid")

    role: Literal["user", "assistant"]
    content: str = Field(max_length=HISTORY_MESSAGE_MAX_CHARS)


class ChatRequest(BaseModel):
    """Body of `POST /chat`."""

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "examples": [
                {"question": "How long is the warranty for the Lumora Thermostat T2?"},
                {
                    "question": "What about the T3?",
                    "history": [
                        {"role": "user", "content": "How long is the T2 warranty?"},
                        {"role": "assistant", "content": "The T2 has a 2-year warranty."},
                    ],
                },
            ]
        },
    )

    question: str = Field(
        min_length=1,
        max_length=QUESTION_MAX_CHARS,
        description="The user's question (1-2000 characters, surrounding whitespace ignored).",
    )
    history: list[ChatMessage] = Field(
        default_factory=list,
        max_length=HISTORY_MAX_MESSAGES,
        description=(
            "Previous messages, oldest first. Optional; only the most recent "
            "RAG_HISTORY_MAX_TURNS turns (server setting, default 6 turns = 12 messages) "
            "are used."
        ),
    )

    @field_validator("question")
    @classmethod
    def _strip_question(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("question must not be blank")
        return stripped


def recent_history(messages: list[ChatMessage], max_turns: int) -> list[ChatMessage]:
    """Keep only the last `max_turns` turns (one user + one assistant message each)."""
    if max_turns <= 0:
        return []
    return messages[-2 * max_turns :]


class SourceResponse(BaseModel):
    """A citation: built by the server from retrieved chunk metadata, never by the LLM."""

    document: str = Field(description="Original PDF file name.")
    page: int = Field(description="1-based page number, as shown in a PDF reader.")
    section: str | None = Field(default=None, description="Detected section heading, if any.")
    snippet: str = Field(description="Start of the cited chunk text (about 300 characters).")
    score: float = Field(description="Retrieval similarity, 0-1 (higher is more relevant).")
    chunk_id: str


class ChatResponse(BaseModel):
    """Body of a successful `POST /chat` response."""

    answer: str
    is_answerable: bool = Field(
        description="False when the documents do not contain the answer (standard refusal)."
    )
    sources: list[SourceResponse]
    model: str
    latency_ms: int

    @classmethod
    def from_result(cls, result: ChatResult) -> ChatResponse:
        """Keep only the contract fields of the chain result."""
        return cls(
            answer=result.answer,
            is_answerable=result.is_answerable,
            sources=[SourceResponse(**source.model_dump()) for source in result.sources],
            model=result.model,
            latency_ms=result.latency_ms,
        )


class HealthResponse(BaseModel):
    """Body of `GET /health`."""

    status: Literal["ok", "unavailable"]
    collection: str
    chunk_count: int | None = Field(
        default=None, description="Chunks in the collection (null when Chroma is unreachable)."
    )
    document_count: int | None = Field(
        default=None, description="Distinct indexed documents (null when Chroma is unreachable)."
    )
    detail: str | None = None


class IngestAccepted(BaseModel):
    """Body of `POST /ingest` when a re-ingestion run was scheduled."""

    status: Literal["accepted"] = "accepted"
    detail: str


class ErrorResponse(BaseModel):
    """Body of every error response except request validation errors (422)."""

    detail: str
    request_id: str | None = None
