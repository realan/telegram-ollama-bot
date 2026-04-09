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


@dataclass(frozen=True, slots=True)
class Settings:
    telegram_bot_token: str
    ollama_base_url: str
    ollama_model: str
    ollama_timeout_seconds: float
    app_log_level: str
    system_prompt_path: Path


def load_settings(dotenv_path: str | Path | None = None) -> Settings:
    load_dotenv(dotenv_path=dotenv_path)

    telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    ollama_model = os.getenv("OLLAMA_MODEL", "").strip()
    ollama_base_url = os.getenv("OLLAMA_BASE_URL", DEFAULT_OLLAMA_BASE_URL).strip()
    app_log_level = os.getenv("APP_LOG_LEVEL", DEFAULT_LOG_LEVEL).strip() or DEFAULT_LOG_LEVEL
    system_prompt_raw = os.getenv("SYSTEM_PROMPT_PATH", str(DEFAULT_SYSTEM_PROMPT_PATH)).strip()
    timeout_raw = os.getenv("OLLAMA_TIMEOUT_SECONDS", str(DEFAULT_TIMEOUT_SECONDS)).strip()

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

    system_prompt_path = Path(system_prompt_raw)
    if not system_prompt_path.is_absolute():
        system_prompt_path = BASE_DIR / system_prompt_path

    if not system_prompt_path.is_file():
        raise ConfigError(f"System prompt file does not exist: {system_prompt_path}")

    return Settings(
        telegram_bot_token=telegram_bot_token,
        ollama_base_url=ollama_base_url,
        ollama_model=ollama_model,
        ollama_timeout_seconds=ollama_timeout_seconds,
        app_log_level=app_log_level.upper(),
        system_prompt_path=system_prompt_path,
    )

