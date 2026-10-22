"""FastAPI application exposing `POST /chat`, `GET /health` and `POST /ingest`.

Run with ``make api`` (or ``uvicorn app.api.main:app --port 8080``); interactive docs are
served at ``/docs``.

Design notes:

- Backend clients (Chroma, embeddings, chat model) live in a single `RagService` created
  by the lifespan and reused by every request.
- Endpoints that do blocking I/O are plain ``def`` functions, so FastAPI runs them in its
  worker thread pool instead of blocking the event loop.
- Every request gets an ID (taken from a well-formed ``X-Request-ID`` header or newly
  generated). It is returned in the ``X-Request-ID`` response header, included in error
  bodies and attached to every log record written while the request is handled.
- Errors never expose stack traces: upstream timeouts/outages map to 503 with a friendly
  message, anything unexpected to 500. Request validation errors keep FastAPI's 422 format.
"""

from __future__ import annotations

import logging
import re
import secrets
import time
import uuid
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
import openai
from fastapi import BackgroundTasks, Depends, FastAPI, Header, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.concurrency import run_in_threadpool
from starlette.responses import Response

from app.api.schemas import (
    ChatRequest,
    ChatResponse,
    ErrorResponse,
    HealthResponse,
    IngestAccepted,
    recent_history,
)
from app.api.service import BackendUnavailableError, RagService
from app.config import MissingOpenAIKeyError, Settings, get_settings
from app.logging_config import configure_logging, request_id_var
from app.rag.schemas import HistoryMessage
from app.retrieval.vectorstore import VectorStoreConfigError

logger = logging.getLogger(__name__)

REQUEST_ID_HEADER = "X-Request-ID"
ADMIN_KEY_HEADER = "X-Admin-Key"
_VALID_REQUEST_ID = re.compile(r"^[A-Za-z0-9._-]{1,64}$")

MSG_LLM_TIMEOUT = "The language model took too long to respond. Please try again in a moment."
MSG_LLM_UNAVAILABLE = (
    "The language model service is temporarily unavailable. Please try again in a moment."
)
MSG_LLM_RATE_LIMITED = "The language model service is busy. Please try again in a moment."
MSG_LLM_MISCONFIGURED = (
    "The assistant is not configured correctly (language model credentials). "
    "Please contact the administrator."
)
MSG_LLM_ERROR = "The language model service returned an error. Please try again later."
MSG_BACKEND_UNAVAILABLE = (
    "A backend service (document index) is temporarily unavailable. Please try again shortly."
)
MSG_BACKEND_MISCONFIGURED = (
    "The document index is not configured correctly. Please contact the administrator."
)
MSG_INTERNAL = "An unexpected error occurred. Please try again later."

# Error responses documented in OpenAPI for /chat.
_CHAT_ERROR_RESPONSES: dict[int | str, dict[str, object]] = {
    502: {"model": ErrorResponse, "description": "The language model returned an error."},
    503: {"model": ErrorResponse, "description": "A backend service is unavailable."},
    500: {"model": ErrorResponse, "description": "Unexpected server error."},
}


# --------------------------------------------------------------------------- helpers


def _request_id(request: Request) -> str | None:
    return getattr(request.state, "request_id", None)


def _error(request: Request, status_code: int, detail: str) -> JSONResponse:
    body = ErrorResponse(detail=detail, request_id=_request_id(request))
    return JSONResponse(status_code=status_code, content=body.model_dump())


def get_service(request: Request) -> RagService:
    """FastAPI dependency returning the shared `RagService` (overridable in tests)."""
    return request.app.state.service


ServiceDep = Annotated[RagService, Depends(get_service)]


# --------------------------------------------------------------------------- handlers


async def _openai_error_handler(request: Request, exc: Exception) -> JSONResponse:
    # Only the class name and status code are logged: provider messages can echo
    # request details, and must never risk leaking credentials into the logs.
    status_code = getattr(exc, "status_code", None)
    if isinstance(exc, openai.APITimeoutError):
        code, detail = status.HTTP_503_SERVICE_UNAVAILABLE, MSG_LLM_TIMEOUT
    elif isinstance(exc, openai.RateLimitError):
        code, detail = status.HTTP_503_SERVICE_UNAVAILABLE, MSG_LLM_RATE_LIMITED
    elif isinstance(exc, openai.AuthenticationError | openai.PermissionDeniedError):
        code, detail = status.HTTP_503_SERVICE_UNAVAILABLE, MSG_LLM_MISCONFIGURED
    elif isinstance(exc, openai.APIConnectionError | openai.InternalServerError):
        code, detail = status.HTTP_503_SERVICE_UNAVAILABLE, MSG_LLM_UNAVAILABLE
    else:
        code, detail = status.HTTP_502_BAD_GATEWAY, MSG_LLM_ERROR
    logger.error(
        "language model call failed",
        extra={
            "error_type": type(exc).__name__,
            "upstream_status": status_code,
            "status_code": code,
        },
    )
    return _error(request, code, detail)


async def _missing_key_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("OPENAI_API_KEY is not configured", extra={"error_type": type(exc).__name__})
    return _error(request, status.HTTP_503_SERVICE_UNAVAILABLE, MSG_LLM_MISCONFIGURED)


async def _backend_unavailable_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error(
        "backend service unavailable",
        extra={"error_type": type(exc).__name__, "error": str(exc)},
    )
    return _error(request, status.HTTP_503_SERVICE_UNAVAILABLE, MSG_BACKEND_UNAVAILABLE)


async def _backend_misconfigured_handler(request: Request, exc: Exception) -> JSONResponse:
    # A permanent problem (e.g. the collection uses the wrong distance metric and must be
    # rebuilt with `--reset`), so the message must not suggest that retrying helps.
    logger.error(
        "vector store is misconfigured",
        extra={"error_type": type(exc).__name__, "error": str(exc)},
    )
    return _error(request, status.HTTP_503_SERVICE_UNAVAILABLE, MSG_BACKEND_MISCONFIGURED)


def _register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(openai.APIError, _openai_error_handler)
    app.add_exception_handler(MissingOpenAIKeyError, _missing_key_handler)
    app.add_exception_handler(VectorStoreConfigError, _backend_misconfigured_handler)
    # Chroma unreachable while creating its client: chromadb raises a plain ValueError,
    # which RagService wraps in BackendUnavailableError.
    app.add_exception_handler(BackendUnavailableError, _backend_unavailable_handler)
    # Chroma unreachable after the client exists: requests fail with httpx transport errors.
    app.add_exception_handler(httpx.TransportError, _backend_unavailable_handler)


# --------------------------------------------------------------------------- middleware


async def _request_context_middleware(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Assign a request ID, log the request and turn unhandled errors into a clean 500."""
    incoming = request.headers.get(REQUEST_ID_HEADER, "")
    request_id = incoming if _VALID_REQUEST_ID.match(incoming) else uuid.uuid4().hex
    request.state.request_id = request_id
    token = request_id_var.set(request_id)
    started = time.perf_counter()
    try:
        try:
            response = await call_next(request)
        except Exception:
            logger.exception(
                "unhandled error", extra={"method": request.method, "path": request.url.path}
            )
            response = _error(request, status.HTTP_500_INTERNAL_SERVER_ERROR, MSG_INTERNAL)
        response.headers[REQUEST_ID_HEADER] = request_id
        logger.info(
            "request completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": int((time.perf_counter() - started) * 1000),
            },
        )
        return response
    finally:
        request_id_var.reset(token)


# --------------------------------------------------------------------------- app


def create_app(settings: Settings | None = None, service: RagService | None = None) -> FastAPI:
    """Build the FastAPI app. `service` can be injected (tests); default: from Settings."""
    s = settings or get_settings()
    configure_logging(s.log_level)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        if getattr(app.state, "service", None) is None:
            app.state.service = RagService(s)
            # Blocking client setup runs off the event loop.
            await run_in_threadpool(app.state.service.warm_up)
        yield

    app = FastAPI(
        title="Lumora Document Assistant API",
        description=(
            "Answers questions from an internal PDF knowledge base with citations "
            "(document name + page). Questions the documents do not cover are refused."
        ),
        version="0.1.0",
        lifespan=lifespan,
    )
    if service is not None:
        app.state.service = service

    _register_exception_handlers(app)
    app.middleware("http")(_request_context_middleware)
    # Added last so it is the outermost middleware and also decorates error responses.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=s.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type", REQUEST_ID_HEADER, ADMIN_KEY_HEADER],
        expose_headers=[REQUEST_ID_HEADER],
    )

    @app.post(
        "/chat",
        response_model=ChatResponse,
        responses=_CHAT_ERROR_RESPONSES,
        summary="Ask a question about the documents",
    )
    def chat(body: ChatRequest, service: ServiceDep) -> ChatResponse:
        # Sync endpoint: FastAPI runs it in the thread pool (the chain is blocking I/O).
        recent = recent_history(body.history, service.settings.rag_history_max_turns)
        history = [HistoryMessage(role=m.role, content=m.content) for m in recent]
        logger.info(
            "chat request",
            extra={"question_chars": len(body.question), "history_messages": len(history)},
        )
        result = service.answer(body.question, history)
        return ChatResponse.from_result(result)

    @app.get(
        "/health",
        response_model=HealthResponse,
        responses={503: {"model": HealthResponse, "description": "Chroma is unreachable."}},
        summary="Check the vector store connection",
    )
    def health(service: ServiceDep) -> HealthResponse | JSONResponse:
        collection = service.settings.chroma_collection
        try:
            chunk_count, document_count = service.index_counts()
        except Exception as exc:  # noqa: BLE001 - any failure means "unhealthy"
            logger.warning(
                "health check failed",
                extra={"error_type": type(exc).__name__, "error": str(exc)},
            )
            body = HealthResponse(
                status="unavailable",
                collection=collection,
                detail="The vector store (Chroma) is unreachable.",
            )
            return JSONResponse(status_code=503, content=body.model_dump())
        return HealthResponse(
            status="ok",
            collection=collection,
            chunk_count=chunk_count,
            document_count=document_count,
        )

    @app.post(
        "/ingest",
        response_model=IngestAccepted,
        status_code=status.HTTP_202_ACCEPTED,
        responses={
            401: {"model": ErrorResponse, "description": "Missing or wrong X-Admin-Key."},
            403: {"model": ErrorResponse, "description": "ADMIN_API_KEY is not configured."},
            409: {"model": ErrorResponse, "description": "An ingestion run is in progress."},
        },
        summary="Re-ingest PDF_DIR in the background (admin only)",
    )
    def ingest_documents(
        request: Request,
        background_tasks: BackgroundTasks,
        service: ServiceDep,
        x_admin_key: Annotated[str | None, Header()] = None,
    ) -> IngestAccepted | JSONResponse:
        admin_key = service.settings.admin_api_key
        if admin_key is None:
            return _error(
                request,
                status.HTTP_403_FORBIDDEN,
                "The ingestion endpoint is disabled. Set ADMIN_API_KEY to enable it.",
            )
        if not x_admin_key or not secrets.compare_digest(
            x_admin_key.encode(), admin_key.get_secret_value().encode()
        ):
            logger.warning("rejected ingest request with a missing or invalid admin key")
            return _error(request, status.HTTP_401_UNAUTHORIZED, "Invalid or missing admin key.")
        if not service.try_start_ingest():
            return _error(
                request, status.HTTP_409_CONFLICT, "An ingestion run is already in progress."
            )
        background_tasks.add_task(service.run_ingest)
        logger.info("ingestion scheduled")
        return IngestAccepted(
            detail="Re-ingestion started in the background; check /health for the chunk count."
        )

    return app


app = create_app()
