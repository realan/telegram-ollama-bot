from __future__ import annotations

import json
import logging
import re

import httpx
from ollama import AsyncClient, ResponseError

from app.memory import Message
from app.utils.exceptions import (
    EmptyModelResponseError,
    InvalidOllamaResponseError,
    ModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)


logger = logging.getLogger(__name__)
SECRET_PATTERNS = (
    re.compile(r"(?i)(telegram_bot_token\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(api[_-]?key\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(password\s*[=:]\s*)([^\s,;]+)"),
    re.compile(r"(?i)(authorization\s*:\s*bearer\s+)([^\s,;]+)"),
    re.compile(r"(?i)(token\s*[=:]\s*)([^\s,;]+)"),
)


class OllamaClient:
    def __init__(
        self,
        base_url: str,
        model: str,
        timeout_seconds: float,
        log_model_context: bool = True,
    ) -> None:
        self._model = model
        self._log_model_context = log_model_context
        self._client = AsyncClient(host=base_url, timeout=timeout_seconds)

    async def generate_reply(self, messages: list[Message], request_type: str) -> str:
        normalized_messages = self._normalize_messages(messages)
        self._log_request_context(
            request_type=request_type,
            messages=normalized_messages,
        )
        try:
            response = await self._client.chat(
                model=self._model,
                messages=normalized_messages,
            )
        except ResponseError as exc:
            logger.exception("ollama request failed")
            if exc.status_code == 404:
                raise ModelNotFoundError(f"Model '{self._model}' was not found") from exc
            raise InvalidOllamaResponseError("Ollama returned an error response") from exc
        except httpx.TimeoutException as exc:
            logger.exception("ollama request failed")
            raise OllamaTimeoutError("Timed out while waiting for Ollama") from exc
        except httpx.HTTPError as exc:
            logger.exception("ollama request failed")
            raise OllamaUnavailableError("Failed to reach Ollama") from exc
        except OSError as exc:
            logger.exception("ollama request failed")
            raise OllamaUnavailableError("Failed to reach Ollama") from exc

        reply_text = getattr(getattr(response, "message", None), "content", None)
        if not isinstance(reply_text, str):
            raise InvalidOllamaResponseError("Ollama returned invalid response payload")

        cleaned_reply = reply_text.strip()
        if not cleaned_reply:
            raise EmptyModelResponseError("Ollama returned an empty response")

        return cleaned_reply

    def _log_request_context(self, request_type: str, messages: list[dict[str, str]]) -> None:
        total_chars = sum(len(message["content"]) for message in messages)
        estimated_tokens = self._estimate_tokens(messages)
        logger.info(
            "ollama request started: type=%s model=%s message_count=%s total_chars=%s estimated_tokens=%s token_count_kind=estimate",
            request_type,
            self._model,
            len(messages),
            total_chars,
            estimated_tokens,
        )
        if self._log_model_context:
            logger.info(
                "ollama request context: type=%s messages=%s",
                request_type,
                json.dumps(self._redact_messages(messages), ensure_ascii=False),
            )

    def _normalize_messages(self, messages: list[Message]) -> list[dict[str, str]]:
        normalized_messages: list[dict[str, str]] = []
        for message in messages:
            role = message["role"]
            content = message["content"]
            if role == "summary":
                normalized_messages.append(
                    {
                        "role": "user",
                        "content": f"Summary of earlier conversation:\n{content}",
                    }
                )
                continue
            normalized_messages.append({"role": role, "content": content})
        return normalized_messages

    def _estimate_tokens(self, messages: list[dict[str, str]]) -> int:
        total_chars = sum(len(message["content"]) for message in messages)
        return max((total_chars + 3) // 4, 1) if messages else 0

    def _redact_messages(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        redacted_messages: list[dict[str, str]] = []
        for message in messages:
            redacted_messages.append(
                {
                    "role": message["role"],
                    "content": self._redact_text(message["content"]),
                }
            )
        return redacted_messages

    def _redact_text(self, text: str) -> str:
        redacted = text
        for pattern in SECRET_PATTERNS:
            redacted = pattern.sub(r"\1[REDACTED]", redacted)
        return redacted
