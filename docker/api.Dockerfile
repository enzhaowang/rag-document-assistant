# FastAPI backend image (also used for one-off ingestion runs).
#
# Build:  docker build -f docker/api.Dockerfile -t rag-api .
# Run:    see docker-compose.yml (needs a Chroma server and OPENAI_API_KEY)

# ---------------------------------------------------------------------------- builder
FROM python:3.11-slim AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    TIKTOKEN_CACHE_DIR=/opt/tiktoken

RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Only the packages the API and the ingestion CLI import are installed, pinned to the exact
# versions in requirements.txt (used as a constraints file). Evaluation-only dependencies
# (ragas, pandas, ...) and the UI (streamlit) stay out of the image.
COPY requirements.txt /tmp/requirements.txt
RUN --mount=type=cache,target=/root/.cache/pip \
    pip install -c /tmp/requirements.txt \
        chromadb fastapi httpx langchain-chroma langchain-core langchain-openai \
        langchain-text-splitters openai pydantic pydantic-settings pymupdf tiktoken \
        "uvicorn[standard]"

# Pre-download the tokenizer used for chunking and context budgeting, so the container
# never needs to fetch it at runtime.
RUN python -c "import tiktoken; tiktoken.get_encoding('cl100k_base')"

# ---------------------------------------------------------------------------- runtime
FROM python:3.11-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH" \
    TIKTOKEN_CACHE_DIR=/opt/tiktoken \
    CHROMA_MODE=http \
    PDF_DIR=/app/data/pdfs

RUN groupadd --system --gid 10001 app \
    && useradd --system --uid 10001 --gid app --home-dir /app --shell /usr/sbin/nologin app

COPY --from=builder /opt/venv /opt/venv
COPY --from=builder /opt/tiktoken /opt/tiktoken

WORKDIR /app
COPY --chown=app:app app/ ./app/
COPY --chown=app:app scripts/check_llm_endpoint.py ./scripts/check_llm_endpoint.py
RUN mkdir -p /app/data/pdfs && chown -R app:app /app

USER app

EXPOSE 8080

HEALTHCHECK --interval=15s --timeout=5s --start-period=30s --retries=5 \
    CMD ["python", "-c", "import sys, urllib.request; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8080/health', timeout=4).status == 200 else 1)"]

CMD ["uvicorn", "app.api.main:app", "--host", "0.0.0.0", "--port", "8080", "--no-access-log"]
