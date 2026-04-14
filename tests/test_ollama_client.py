from __future__ import annotations

import logging

import pytest

from app.clients.ollama_client import OllamaClient
from app.utils.exceptions import (
    EmptyModelResponseError,
    InvalidOllamaResponseError,
)


class StubAsyncChatClient:
    def __init__(self, response: dict[str, object]) -> None:
        self.response = response
        self.calls: list[dict[str, object]] = []

    async def chat(self, *, model: str, messages: list[dict[str, str]]) -> dict[str, object]:
        self.calls.append({"model": model, "messages": messages})
        return self.response


@pytest.mark.asyncio
async def test_ollama_client_logs_request_context_and_size_metrics(caplog: pytest.LogCaptureFixture) -> None:
    client = OllamaClient(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        timeout_seconds=30,
        log_model_context=True,
    )
    stub = StubAsyncChatClient({"message": {"content": "reply"}})
    client._client = stub

    with caplog.at_level(logging.INFO):
        result = await client.generate_reply(
            messages=[
                {"role": "system", "content": "You are helpful"},
                {"role": "summary", "content": "Older facts"},
                {"role": "user", "content": "Hello there"},
            ],
            request_type="summary_generation",
        )

    assert result == "reply"
    assert stub.calls == [
        {
            "model": "llama3.1:8b",
            "messages": [
                {"role": "system", "content": "You are helpful"},
                {
                    "role": "user",
                    "content": "Summary of earlier conversation:\nOlder facts",
                },
                {"role": "user", "content": "Hello there"},
            ],
        }
    ]
    assert "type=summary_generation" in caplog.text
    assert "message_count=3" in caplog.text
    assert "total_chars=70" in caplog.text
    assert "estimated_tokens=18" in caplog.text
    assert "token_count_kind=estimate" in caplog.text
    assert '"role": "system"' in caplog.text
    assert 'Summary of earlier conversation:\\nOlder facts' in caplog.text


@pytest.mark.asyncio
async def test_ollama_client_redacts_secrets_from_logged_context(caplog: pytest.LogCaptureFixture) -> None:
    client = OllamaClient(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        timeout_seconds=30,
        log_model_context=True,
    )
    client._client = StubAsyncChatClient({"message": {"content": "reply"}})

    secret_message = (
        "token=supersecret TELEGRAM_BOT_TOKEN=bot-secret "
        "Authorization: Bearer bearer-secret password=hunter2 api_key=key-secret"
    )

    with caplog.at_level(logging.INFO):
        await client.generate_reply(
            messages=[{"role": "user", "content": secret_message}],
            request_type="regular_reply",
        )

    assert "supersecret" not in caplog.text
    assert "bot-secret" not in caplog.text
    assert "bearer-secret" not in caplog.text
    assert "hunter2" not in caplog.text
    assert "key-secret" not in caplog.text
    assert "[REDACTED]" in caplog.text


@pytest.mark.asyncio
async def test_ollama_client_can_disable_full_context_logging(caplog: pytest.LogCaptureFixture) -> None:
    client = OllamaClient(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        timeout_seconds=30,
        log_model_context=False,
    )
    client._client = StubAsyncChatClient({"message": {"content": "reply"}})

    with caplog.at_level(logging.INFO):
        await client.generate_reply(
            messages=[{"role": "user", "content": "hello"}],
            request_type="regular_reply",
        )

    assert "ollama request started" in caplog.text
    assert "ollama request context" not in caplog.text


@pytest.mark.asyncio
async def test_ollama_client_rejects_invalid_chat_payload() -> None:
    client = OllamaClient(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        timeout_seconds=30,
    )
    client._client = StubAsyncChatClient({"response": "missing message payload"})

    with pytest.raises(InvalidOllamaResponseError):
        await client.generate_reply(
            messages=[{"role": "user", "content": "hello"}],
            request_type="regular_reply",
        )


@pytest.mark.asyncio
async def test_ollama_client_rejects_empty_chat_reply() -> None:
    client = OllamaClient(
        base_url="http://localhost:11434",
        model="llama3.1:8b",
        timeout_seconds=30,
    )
    client._client = StubAsyncChatClient({"message": {"content": "   "}})

    with pytest.raises(EmptyModelResponseError):
        await client.generate_reply(
            messages=[{"role": "user", "content": "hello"}],
            request_type="regular_reply",
        )
