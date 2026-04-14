from __future__ import annotations

from pathlib import Path

import pytest

from app.config import load_settings
from app.utils.exceptions import ConfigError


def test_load_settings_reads_env(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("system", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("summarize", encoding="utf-8")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setenv("OLLAMA_BASE_URL", "http://example.com")
    monkeypatch.setenv("OLLAMA_TIMEOUT_SECONDS", "42")
    monkeypatch.setenv("APP_LOG_LEVEL", "debug")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(prompt_path))
    monkeypatch.setenv("SUMMARIZATION_PROMPT_PATH", str(summary_prompt_path))
    monkeypatch.setenv("MAX_HISTORY_MESSAGES", "12")
    monkeypatch.setenv("MAX_CONTEXT_CHARS", "5000")
    monkeypatch.setenv("SUMMARY_TRIGGER_MESSAGES", "5")
    monkeypatch.setenv("SUMMARY_MAX_CHARS", "900")
    monkeypatch.setenv("LOG_MODEL_CONTEXT", "false")

    settings = load_settings()

    assert settings.telegram_bot_token == "token"
    assert settings.ollama_model == "llama3.1:8b"
    assert settings.ollama_base_url == "http://example.com"
    assert settings.ollama_timeout_seconds == 42
    assert settings.app_log_level == "DEBUG"
    assert settings.system_prompt_path == prompt_path
    assert settings.summarization_prompt_path == summary_prompt_path
    assert settings.max_history_messages == 12
    assert settings.max_context_chars == 5000
    assert settings.summary_trigger_messages == 5
    assert settings.summary_max_chars == 900
    assert settings.log_model_context is False


def test_load_settings_requires_prompt_file(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "/tmp/missing-prompt.txt")
    monkeypatch.setenv("SUMMARIZATION_PROMPT_PATH", "/tmp/missing-summary-prompt.txt")

    with pytest.raises(ConfigError):
        load_settings()


@pytest.mark.parametrize(
    ("env_name", "env_value", "expected_message"),
    [
        ("MAX_HISTORY_MESSAGES", "abc", "MAX_HISTORY_MESSAGES must be an integer"),
        ("MAX_HISTORY_MESSAGES", "1", "MAX_HISTORY_MESSAGES must be greater than or equal to 2"),
        ("MAX_CONTEXT_CHARS", "abc", "MAX_CONTEXT_CHARS must be an integer"),
        ("MAX_CONTEXT_CHARS", "0", "MAX_CONTEXT_CHARS must be greater than 0"),
        ("SUMMARY_TRIGGER_MESSAGES", "abc", "SUMMARY_TRIGGER_MESSAGES must be an integer"),
        (
            "SUMMARY_TRIGGER_MESSAGES",
            "1",
            "SUMMARY_TRIGGER_MESSAGES must be greater than or equal to 2",
        ),
        ("SUMMARY_MAX_CHARS", "abc", "SUMMARY_MAX_CHARS must be an integer"),
        ("SUMMARY_MAX_CHARS", "0", "SUMMARY_MAX_CHARS must be greater than 0"),
        ("LOG_MODEL_CONTEXT", "maybe", "LOG_MODEL_CONTEXT must be a boolean"),
    ],
)
def test_load_settings_validates_context_limits(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
    env_name: str,
    env_value: str,
    expected_message: str,
) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("system", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("summarize", encoding="utf-8")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(prompt_path))
    monkeypatch.setenv("SUMMARIZATION_PROMPT_PATH", str(summary_prompt_path))
    monkeypatch.setenv(env_name, env_value)

    with pytest.raises(ConfigError, match=expected_message):
        load_settings()


def test_load_settings_requires_summary_trigger_less_than_history_limit(
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("system", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("summarize", encoding="utf-8")

    monkeypatch.setenv("TELEGRAM_BOT_TOKEN", "token")
    monkeypatch.setenv("OLLAMA_MODEL", "llama3.1:8b")
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(prompt_path))
    monkeypatch.setenv("SUMMARIZATION_PROMPT_PATH", str(summary_prompt_path))
    monkeypatch.setenv("MAX_HISTORY_MESSAGES", "5")
    monkeypatch.setenv("SUMMARY_TRIGGER_MESSAGES", "5")

    with pytest.raises(
        ConfigError,
        match="SUMMARY_TRIGGER_MESSAGES must be less than MAX_HISTORY_MESSAGES",
    ):
        load_settings()
