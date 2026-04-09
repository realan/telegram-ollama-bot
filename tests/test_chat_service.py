from __future__ import annotations

from pathlib import Path

import pytest

from app.services.chat_service import ChatService
from app.utils.exceptions import OllamaTimeoutError, ValidationError


class StubOllamaClient:
    def __init__(self, reply: str | None = None, error: Exception | None = None) -> None:
        self.reply = reply
        self.error = error
        self.calls: list[tuple[str, str | None]] = []

    async def generate_reply(self, user_message: str, system_prompt: str | None) -> str:
        self.calls.append((user_message, system_prompt))
        if self.error:
            raise self.error
        assert self.reply is not None
        return self.reply


@pytest.mark.asyncio
async def test_chat_service_returns_model_reply(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    client = StubOllamaClient(reply="model reply")
    service = ChatService(client, prompt_path)

    result = await service.handle_user_message("  hello  ")

    assert result == "model reply"
    assert client.calls == [("hello", "You are helpful")]


@pytest.mark.asyncio
async def test_chat_service_rejects_empty_text(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    client = StubOllamaClient(reply="unused")
    service = ChatService(client, prompt_path)

    with pytest.raises(ValidationError):
        await service.handle_user_message("   ")


@pytest.mark.asyncio
async def test_chat_service_propagates_ollama_errors(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    client = StubOllamaClient(error=OllamaTimeoutError("timeout"))
    service = ChatService(client, prompt_path)

    with pytest.raises(OllamaTimeoutError):
        await service.handle_user_message("hello")

