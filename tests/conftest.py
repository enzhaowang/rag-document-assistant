"""Shared pytest fixtures."""

from collections.abc import Iterator
from pathlib import Path

import pytest

from app.config import Settings, get_settings


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> Iterator[Path]:
    """Isolate a test from the developer's shell environment and repository `.env`.

    Removes every Settings-related environment variable, switches the working directory
    to an empty temp dir (so no `.env` is picked up) and clears the settings cache.
    Yields the temp dir so tests can write their own `.env` into it.
    """
    for name in Settings.model_fields:
        monkeypatch.delenv(name.upper(), raising=False)
    monkeypatch.chdir(tmp_path)
    get_settings.cache_clear()
    yield tmp_path
    get_settings.cache_clear()
