"""Smoke-check the configured OpenAI-compatible endpoint before running the pipeline.

Makes a few real (cheap) API calls with the models from `.env` and reports whether
each capability the project relies on works:

1. Embeddings (P3 ingestion and retrieval)
2. Plain chat completion (P4 question rewriting)
3. Structured output via function calling (P4 answers with cited chunk IDs)

Usage: make check-llm  (or: python -m scripts.check_llm_endpoint)
"""

import sys

from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from pydantic import BaseModel

from app.config import get_settings


class _Probe(BaseModel):
    is_answerable: bool
    answer: str
    cited_chunk_ids: list[str]


def main() -> int:
    settings = get_settings()
    print(f"Chat endpoint:      {settings.openai_base_url} ({settings.openai_chat_model})")
    print(f"Embedding endpoint: {settings.embedding_base_url} ({settings.openai_embedding_model})")

    embeddings = OpenAIEmbeddings(
        model=settings.openai_embedding_model,
        base_url=settings.embedding_base_url,
        api_key=settings.require_embedding_api_key(),
        # Send raw text instead of tiktoken IDs; many OpenAI-compatible APIs reject IDs.
        check_embedding_ctx_length=False,
    )
    llm = ChatOpenAI(
        model=settings.openai_chat_model,
        base_url=settings.openai_base_url,
        api_key=settings.require_openai_api_key(),
        temperature=0,
        timeout=30,
        max_retries=1,
    )

    def check_embeddings() -> str:
        vectors = embeddings.embed_documents(["Return policy: 30 days.", "Warranty: 2 years."])
        return f"{len(vectors)} vectors, dim={len(vectors[0])}"

    def check_chat() -> str:
        reply = llm.invoke("Reply with the single word: pong")
        model = reply.response_metadata.get("model_name", "unknown")
        return f"{str(reply.content).strip()!r} (served by {model})"

    def check_structured() -> str:
        structured = llm.with_structured_output(_Probe, method="function_calling")
        result = structured.invoke(
            "Context: [doc1__p1__c0] The return window is 30 days.\n"
            "Question: How long is the return window? Cite the chunk ID you used."
        )
        return repr(result)

    failures = 0
    for name, check in [
        ("embeddings", check_embeddings),
        ("chat", check_chat),
        ("structured output", check_structured),
    ]:
        try:
            print(f"[OK]   {name}: {check()}")
        except Exception as exc:  # noqa: BLE001 - report every failure, keep going
            failures += 1
            print(f"[FAIL] {name}: {type(exc).__name__}: {exc}")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
