from __future__ import annotations

import logging

import httpx
from ollama import AsyncClient, ResponseError

from app.utils.exceptions import (
    EmptyModelResponseError,
    InvalidOllamaResponseError,
    ModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)


logger = logging.getLogger(__name__)


class OllamaClient:
    def __init__(self, base_url: str, model: str, timeout_seconds: float) -> None:
        self._model = model
        self._client = AsyncClient(host=base_url, timeout=timeout_seconds)

    async def generate_reply(self, user_message: str, system_prompt: str | None) -> str:
        logger.info("ollama request started", extra={"model": self._model})
        try:
            response = await self._client.generate(
                model=self._model,
                prompt=user_message,
                system=system_prompt,
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

        reply_text = response.get("response")
        if not isinstance(reply_text, str):
            raise InvalidOllamaResponseError("Ollama returned invalid response payload")

        cleaned_reply = reply_text.strip()
        if not cleaned_reply:
            raise EmptyModelResponseError("Ollama returned an empty response")

        return cleaned_reply

