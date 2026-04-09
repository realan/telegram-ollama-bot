from __future__ import annotations

from pathlib import Path

import pytest

from app.config import load_settings
from app.utils.exceptions import ConfigError


def test_load_settings_reads_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("system", encoding="utf-8")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://example.com")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "42")
    monkeypatch.setenv("APP_LOG_LEVEL", "debug")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(prompt_path))

    settings = load_settings()

    assert settings.telegram_bot_token == "token"
    assert settings.ollama_model == "llama3.1:8b"
    assert settings.ollama_base_url == "http://example.com"
    assert settings.ollama_timeout_seconds == 42
    assert settings.app_log_level == "DEBUG"
    assert settings.system_prompt_path == prompt_path


def test_load_settings_requires_prompt_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "/tmp/missing-prompt.txt")

    with pytest.raises(ConfigError):
        load_settings()

