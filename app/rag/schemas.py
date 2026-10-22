"""Structured output schemas for the LLM and the chain result.

- `LLMAnswer` is what the chat model must return (via function calling). The model only
  *proposes* chunk IDs; the chain validates them against the chunks it actually sent.
- `ChatResult` is what `answer_question()` returns. Its first five fields mirror the
  `/chat` response contract; the remaining fields are diagnostics for logging and
  evaluation.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field


class LLMAnswer(BaseModel):
    """Structured answer produced by the chat model."""

    is_answerable: bool = Field(
        description=(
            "True only if the provided excerpts contain the information needed to answer "
            "the question. False if the information is missing or the question is out of "
            "scope."
        )
    )
    answer: str = Field(
        description=(
            "The answer in plain text, based only on the excerpts. Empty string when "
            "is_answerable is false."
        )
    )
    cited_chunk_ids: list[str] = Field(
        default_factory=list,
        description=(
            "IDs of the excerpts used, copied exactly from the [chunk_id] labels. When "
            "is_answerable is false: IDs of related excerpts, or an empty list."
        ),
    )


class HistoryMessage(BaseModel):
    """One previous message of the conversation."""

    role: Literal["user", "assistant"]
    content: str


class Source(BaseModel):
    """A citation shown to the user. Built by code from retrieved chunk metadata."""

    document: str
    page: int
    section: str | None = None
    snippet: str
    score: float
    chunk_id: str


class RefusalReason(StrEnum):
    """Why an answer was refused (`is_answerable=False`)."""

    NO_RELEVANT_CHUNKS = "no_relevant_chunks"  # nothing passed the retrieval threshold
    MODEL_DECLINED = "model_declined"  # the LLM said the context does not answer it
    NO_VALID_CITATIONS = "no_valid_citations"  # LLM claimed an answer but cited nothing valid
    INVALID_MODEL_OUTPUT = "invalid_model_output"  # the LLM did not return the schema


class ChatResult(BaseModel):
    """Result of `answer_question()`."""

    answer: str
    is_answerable: bool
    sources: list[Source] = Field(default_factory=list)
    model: str
    latency_ms: int

    # Diagnostics (not part of the /chat response contract).
    standalone_question: str
    refusal_reason: RefusalReason | None = None
    contexts: list[str] = Field(
        default_factory=list, description="Texts of the chunks sent to the LLM, in order."
    )
