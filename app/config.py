from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os

from dotenv import load_dotenv

from app.utils.exceptions import ConfigError


BASE_DIR = Path(__file__).resolve().parent.parent
DEFAULT_OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_TIMEOUT_SECONDS = 120
DEFAULT_LOG_LEVEL = "INFO"
DEFAULT_SYSTEM_PROMPT_PATH = Path("app/prompts/system_prompt.txt")
DEFAULT_SUMMARIZATION_PROMPT_PATH = Path("app/prompts/summarization_prompt.txt")
DEFAULT_MAX_HISTORY_MESSAGES = 10
DEFAULT_MAX_CONTEXT_CHARS = 4000
DEFAULT_SUMMARY_TRIGGER_MESSAGES = 5
DEFAULT_SUMMARY_MAX_CHARS = 800
DEFAULT_LOG_MODEL_CONTEXT = True


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: float
    app_log_level: str
    system_prompt_path: Path
    summarization_prompt_path: Path
    max_history_messages: int
    max_context_chars: int
    summary_trigger_messages: int
    summary_max_chars: int
    log_model_context: bool


def load_settings(dotenv_path: str | Path | None = None) -> Settings:
    load_dotenv(dotenv_path=dotenv_path)

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    ollama_model = os.getenv("OLLAMA_MODEL", "").strip()
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).strip()
    app_log_level = os.getenv("APP_LOG_LEVEL", DEFAULT_LOG_LEVEL).strip() or DEFAULT_LOG_LEVEL
    system_prompt_raw = os.getenv("SYSTEM_PROMPT_PATH", str(DEFAULT_SYSTEM_PROMPT_PATH)).strip()
    summarization_prompt_raw = os.getenv(
        "SUMMARIZATION_PROMPT_PATH",
        str(DEFAULT_SUMMARIZATION_PROMPT_PATH),
    ).strip()
    timeout_raw = os.getenv("OLLAMA_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)).strip()
    max_history_messages_raw = os.getenv(
        "MAX_HISTORY_MESSAGES",
        str(DEFAULT_MAX_HISTORY_MESSAGES),
    ).strip()
    max_context_chars_raw = os.getenv(
        "MAX_CONTEXT_CHARS",
        str(DEFAULT_MAX_CONTEXT_CHARS),
    ).strip()
    summary_trigger_messages_raw = os.getenv(
        "SUMMARY_TRIGGER_MESSAGES",
        str(DEFAULT_SUMMARY_TRIGGER_MESSAGES),
    ).strip()
    summary_max_chars_raw = os.getenv(
        "SUMMARY_MAX_CHARS",
        str(DEFAULT_SUMMARY_MAX_CHARS),
    ).strip()
    log_model_context_raw = os.getenv(
        "LOG_MODEL_CONTEXT",
        str(DEFAULT_LOG_MODEL_CONTEXT).lower(),
    ).strip()

    if not telegram_bot_token:
        raise ConfigError("TELEGRAM_BOT_TOKEN is required")
    if not ollama_model:
        raise ConfigError("OLLAMA_MODEL is required")

    try:
        ollama_timeout_seconds = float(timeout_raw)
    except ValueError as exc:
        raise ConfigError("OLLAMA_TIMEOUT_SECONDS must be a number") from exc

    if ollama_timeout_seconds <= 0:
        raise ConfigError("OLLAMA_TIMEOUT_SECONDS must be greater than 0")

    try:
        max_history_messages = int(max_history_messages_raw)
    except ValueError as exc:
        raise ConfigError("MAX_HISTORY_MESSAGES must be an integer") from exc

    if max_history_messages < 2:
        raise ConfigError("MAX_HISTORY_MESSAGES must be greater than or equal to 2")

    try:
        max_context_chars = int(max_context_chars_raw)
    except ValueError as exc:
        raise ConfigError("MAX_CONTEXT_CHARS must be an integer") from exc

    if max_context_chars <= 0:
        raise ConfigError("MAX_CONTEXT_CHARS must be greater than 0")

    system_prompt_path = Path(system_prompt_raw)
    if not system_prompt_path.is_absolute():
        system_prompt_path = BASE_DIR / system_prompt_path

    if not system_prompt_path.is_file():
        raise ConfigError(f"System prompt file does not exist: {system_prompt_path}")

    summarization_prompt_path = Path(summarization_prompt_raw)
    if not summarization_prompt_path.is_absolute():
        summarization_prompt_path = BASE_DIR / summarization_prompt_path

    if not summarization_prompt_path.is_file():
        raise ConfigError(
            "Summarization prompt file does not exist: "
            f"{summarization_prompt_path}"
        )

    try:
        summary_trigger_messages = int(summary_trigger_messages_raw)
    except ValueError as exc:
        raise ConfigError("SUMMARY_TRIGGER_MESSAGES must be an integer") from exc

    if summary_trigger_messages < 2:
        raise ConfigError("SUMMARY_TRIGGER_MESSAGES must be greater than or equal to 2")
    if summary_trigger_messages >= max_history_messages:
        raise ConfigError("SUMMARY_TRIGGER_MESSAGES must be less than MAX_HISTORY_MESSAGES")

    try:
        summary_max_chars = int(summary_max_chars_raw)
    except ValueError as exc:
        raise ConfigError("SUMMARY_MAX_CHARS must be an integer") from exc

    if summary_max_chars <= 0:
        raise ConfigError("SUMMARY_MAX_CHARS must be greater than 0")

    log_model_context = _parse_bool_env(
        name="LOG_MODEL_CONTEXT",
        value=log_model_context_raw,
    )

    return Settings(
        telegram_bot_token=telegram_bot_token,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        ollama_timeout_seconds=ollama_timeout_seconds,
        app_log_level=app_log_level.upper(),
        system_prompt_path=system_prompt_path,
        summarization_prompt_path=summarization_prompt_path,
        max_history_messages=max_history_messages,
        max_context_chars=max_context_chars,
        summary_trigger_messages=summary_trigger_messages,
        summary_max_chars=summary_max_chars,
        log_model_context=log_model_context,
    )


def _parse_bool_env(name: str, value: str) -> bool:
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ConfigError(f"{name} must be a boolean")
