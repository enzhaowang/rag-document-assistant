"""Smoke tests for configuration loading and structured logging."""

import json
import logging
from pathlib import Path

import pytest
from pydantic import ValidationError

from app.config import MissingOpenAIKeyError, Settings, get_settings
from app.logging_config import JsonFormatter, configure_logging

REPO_ROOT = Path(__file__).resolve().parents[1]


def _env_example_keys() -> list[str]:
    keys = []
    for line in (REPO_ROOT / ".env.example").read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#"):
            keys.append(line.split("=", 1)[0].strip())
    return keys


def test_settings_load_without_env_file_or_api_key(clean_env: Path) -> None:
    settings = get_settings()

    assert settings.openai_api_key is None
    assert settings.chroma_mode == "local"
    assert settings.chunk_size_tokens == 500
    assert settings.chunk_overlap_tokens == 80
    assert settings.retrieval_top_k == 6
    assert settings.log_level == "INFO"


def test_get_settings_is_cached(clean_env: Path) -> None:
    assert get_settings() is get_settings()


def test_environment_variables_override_defaults(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CHROMA_MODE", "http")
    monkeypatch.setenv("CHROMA_PORT", "9000")
    monkeypatch.setenv("RETRIEVAL_SCORE_THRESHOLD", "0.5")
    monkeypatch.setenv("PDF_DIR", "/srv/pdfs")

    settings = Settings()

    assert settings.chroma_mode == "http"
    assert settings.chroma_port == 9000
    assert settings.retrieval_score_threshold == 0.5
    assert settings.pdf_dir == Path("/srv/pdfs")


def test_dotenv_file_is_read_and_env_wins(clean_env: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (clean_env / ".env").write_text("OPENAI_CHAT_MODEL=model-from-dotenv\nCHROMA_COLLECTION=a\n")
    monkeypatch.setenv("CHROMA_COLLECTION", "b")

    settings = Settings()

    assert settings.openai_chat_model == "model-from-dotenv"
    assert settings.chroma_collection == "b"


def test_env_example_matches_settings_fields() -> None:
    keys = _env_example_keys()

    assert len(keys) == len(set(keys)), "duplicate keys in .env.example"
    assert sorted(k.lower() for k in keys) == sorted(Settings.model_fields)


def test_env_example_values_are_valid_and_match_defaults(clean_env: Path) -> None:
    (clean_env / ".env").write_text((REPO_ROOT / ".env.example").read_text())

    from_example = Settings()
    defaults = Settings(_env_file=None)

    # The example leaves the keys blank; every other value documents the default.
    secrets = {"openai_api_key", "openai_embedding_api_key"}
    assert from_example.model_dump(exclude=secrets) == defaults.model_dump(exclude=secrets)


@pytest.mark.parametrize("value", [None, "", "   "])
def test_require_openai_api_key_raises_clear_error(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch, value: str | None
) -> None:
    if value is not None:
        monkeypatch.setenv("OPENAI_API_KEY", value)

    with pytest.raises(MissingOpenAIKeyError, match="OPENAI_API_KEY is not set"):
        Settings().require_openai_api_key()


def test_api_key_is_returned_but_never_printed(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-test-secret")

    settings = Settings()

    assert settings.require_openai_api_key() == "sk-test-secret"
    assert "sk-test-secret" not in repr(settings)
    assert "sk-test-secret" not in str(settings)


def test_embedding_endpoint_falls_back_to_chat_endpoint(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-chat")
    monkeypatch.setenv("OPENAI_BASE_URL", "https://openrouter.ai/api/v1")
    monkeypatch.setenv("OPENAI_EMBEDDING_BASE_URL", "")
    monkeypatch.setenv("OPENAI_EMBEDDING_API_KEY", "  ")

    settings = Settings()

    assert settings.embedding_base_url == "https://openrouter.ai/api/v1"
    assert settings.require_embedding_api_key() == "sk-chat"


def test_embedding_endpoint_overrides_are_used(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "sk-chat")
    monkeypatch.setenv("OPENAI_EMBEDDING_BASE_URL", "https://embeddings.example/v1")
    monkeypatch.setenv("OPENAI_EMBEDDING_API_KEY", "sk-embed")

    settings = Settings()

    assert settings.openai_base_url == "https://api.openai.com/v1"
    assert settings.embedding_base_url == "https://embeddings.example/v1"
    assert settings.require_embedding_api_key() == "sk-embed"
    assert "sk-embed" not in repr(settings)


def test_embedding_key_without_any_key_raises(clean_env: Path) -> None:
    with pytest.raises(MissingOpenAIKeyError, match="OPENAI_API_KEY is not set"):
        Settings().require_embedding_api_key()


@pytest.mark.parametrize(
    ("name", "value"),
    [
        ("CHROMA_MODE", "cloud"),
        ("LOG_LEVEL", "VERBOSE"),
        ("CHUNK_SIZE_TOKENS", "0"),
        ("RETRIEVAL_SCORE_THRESHOLD", "1.5"),
        ("CHROMA_PORT", "not-a-port"),
    ],
)
def test_invalid_values_are_rejected(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch, name: str, value: str
) -> None:
    monkeypatch.setenv(name, value)

    with pytest.raises(ValidationError):
        Settings()


def test_overlap_must_be_smaller_than_chunk_size(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("CHUNK_SIZE_TOKENS", "100")
    monkeypatch.setenv("CHUNK_OVERLAP_TOKENS", "100")

    with pytest.raises(ValidationError, match="CHUNK_OVERLAP_TOKENS must be smaller"):
        Settings()


def test_json_formatter_emits_one_json_object_with_extras() -> None:
    record = logging.LogRecord("app.test", logging.INFO, __file__, 1, "hello %s", ("world",), None)
    record.request_id = "abc123"

    line = JsonFormatter().format(record)
    payload = json.loads(line)

    assert "\n" not in line
    assert payload["message"] == "hello world"
    assert payload["level"] == "INFO"
    assert payload["logger"] == "app.test"
    assert payload["request_id"] == "abc123"
    assert "ts" in payload


def test_configure_logging_uses_log_level_setting_and_is_idempotent(
    clean_env: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("LOG_LEVEL", "WARNING")
    root = logging.getLogger()
    original_level, original_handlers = root.level, list(root.handlers)
    try:
        configure_logging()
        configure_logging()

        json_handlers = [h for h in root.handlers if isinstance(h.formatter, JsonFormatter)]
        assert len(json_handlers) == 1
        assert root.level == logging.WARNING
    finally:
        root.handlers[:] = original_handlers
        root.setLevel(original_level)
