from __future__ import annotations

from pathlib import Path

import pytest

from app.memory import InMemoryConversationStore
from app.services.chat_service import ChatService


class StubOllamaClient:
    def __init__(self, reply: str = "ok") -> None:
        self.reply = reply

    async def generate_reply(self, messages: list[dict[str, str]], request_type: str) -> str:
        return self.reply


def create_service(
    store: InMemoryConversationStore,
    prompt_path: Path,
    summarization_prompt_path: Path,
) -> ChatService:
    return ChatService(
        ollama_client=StubOllamaClient(),  # type: ignore[arg-type]
        system_prompt_path=prompt_path,
        summarization_prompt_path=summarization_prompt_path,
        conversation_store=store,
        max_history_messages=10,
        max_context_chars=4000,
        summary_trigger_messages=5,
        summary_max_chars=800,
    )


@pytest.mark.asyncio
async def test_clear_empties_history(tmp_path: Path) -> None:
    prompt = tmp_path / "system.txt"
    prompt.write_text("system")
    summary_prompt = tmp_path / "summary.txt"
    summary_prompt.write_text("summarize")

    store = InMemoryConversationStore()
    service = create_service(store, prompt, summary_prompt)

    await service.handle_user_message(1, "привет")
    assert await store.read(1) != []

    await store.clear(1)
    assert await store.read(1) == []


@pytest.mark.asyncio
async def test_clear_does_not_affect_other_user(tmp_path: Path) -> None:
    prompt = tmp_path / "system.txt"
    prompt.write_text("system")
    summary_prompt = tmp_path / "summary.txt"
    summary_prompt.write_text("summarize")

    store = InMemoryConversationStore()
    service = create_service(store, prompt, summary_prompt)

    await service.handle_user_message(1, "сообщение от первого")
    await service.handle_user_message(2, "сообщение от второго")

    await store.clear(1)

    assert await store.read(1) == []
    assert await store.read(2) != []


@pytest.mark.asyncio
async def test_clear_on_empty_history_does_not_raise(tmp_path: Path) -> None:
    store = InMemoryConversationStore()
    await store.clear(42)
    assert await store.read(42) == []


@pytest.mark.asyncio
async def test_next_request_after_clear_has_no_previous_context(tmp_path: Path) -> None:
    prompt = tmp_path / "system.txt"
    prompt.write_text("system")
    summary_prompt = tmp_path / "summary.txt"
    summary_prompt.write_text("summarize")

    calls: list[list[dict[str, str]]] = []

    class TrackingClient:
        async def generate_reply(self, messages: list[dict[str, str]], request_type: str) -> str:
            calls.append(list(messages))
            return "ответ"

    store = InMemoryConversationStore()
    service = ChatService(
        ollama_client=TrackingClient(),  # type: ignore[arg-type]
        system_prompt_path=prompt,
        summarization_prompt_path=summary_prompt,
        conversation_store=store,
        max_history_messages=10,
        max_context_chars=4000,
        summary_trigger_messages=5,
        summary_max_chars=800,
    )

    await service.handle_user_message(1, "первое сообщение")
    await store.clear(1)
    calls.clear()

    await service.handle_user_message(1, "второе сообщение")

    # В контексте должны быть только system prompt и новое сообщение
    assert len(calls) == 1
    context = calls[0]
    roles = [m["role"] for m in context]
    assert roles == ["system", "user"]
    assert context[-1]["content"] == "второе сообщение"
