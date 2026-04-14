from __future__ import annotations

from pathlib import Path

import pytest

from app.memory import InMemoryConversationStore
from app.services.chat_service import ChatService
from app.utils.exceptions import OllamaTimeoutError, ValidationError


class StubOllamaClient:
    def __init__(
        self,
        reply: str | None = None,
        *,
        replies: list[str] | None = None,
        error: Exception | None = None,
    ) -> None:
        self.reply = reply
        self.replies = list(replies or [])
        self.error = error
        self.calls: list[tuple[list[dict[str, str]], str]] = []

    async def generate_reply(self, messages: list[dict[str, str]], request_type: str) -> str:
        self.calls.append((messages, request_type))
        if self.error:
            raise self.error
        if self.replies:
            return self.replies.pop(0)
        assert self.reply is not None
        return self.reply


def create_service(
    client: StubOllamaClient,
    prompt_path: Path,
    summarization_prompt_path: Path,
    store: InMemoryConversationStore,
    *,
    max_history_messages: int = 10,
    max_context_chars: int = 4000,
    summary_trigger_messages: int = 5,
    summary_max_chars: int = 800,
) -> ChatService:
    return ChatService(
        client,
        prompt_path,
        summarization_prompt_path,
        store,
        max_history_messages=max_history_messages,
        max_context_chars=max_context_chars,
        summary_trigger_messages=summary_trigger_messages,
        summary_max_chars=summary_max_chars,
    )


@pytest.mark.asyncio
async def test_chat_service_returns_model_reply(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize", encoding="utf-8")
    client = StubOllamaClient(reply="model reply")
    store = InMemoryConversationStore()
    service = create_service(client, prompt_path, summary_prompt_path, store)

    result = await service.handle_user_message(1, "  hello  ")

    assert result == "model reply"
    assert client.calls == [
        (
            [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "hello"},
            ],
            "regular_reply",
        )
    ]
    assert await store.read(1) == [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "model reply"},
    ]


@pytest.mark.asyncio
async def test_chat_service_rejects_empty_text(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize", encoding="utf-8")
    client = StubOllamaClient(reply="unused")
    service = create_service(client, prompt_path, summary_prompt_path, InMemoryConversationStore())

    with pytest.raises(ValidationError):
        await service.handle_user_message(1, "   ")


@pytest.mark.asyncio
async def test_chat_service_propagates_ollama_errors(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize", encoding="utf-8")
    client = StubOllamaClient(error=OllamaTimeoutError("timeout"))
    store = InMemoryConversationStore()
    service = create_service(client, prompt_path, summary_prompt_path, store)

    with pytest.raises(OllamaTimeoutError):
        await service.handle_user_message(1, "hello")
    assert await store.read(1) == []


@pytest.mark.asyncio
async def test_chat_service_uses_only_current_user_history(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize", encoding="utf-8")
    client = StubOllamaClient(reply="second reply")
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "user", "content": "first question"},
            {"role": "assistant", "content": "first answer"},
        ],
    )
    await store.append_many(
        2,
        [
            {"role": "user", "content": "other user question"},
            {"role": "assistant", "content": "other user answer"},
        ],
    )
    service = create_service(client, prompt_path, summary_prompt_path, store)

    result = await service.handle_user_message(1, "follow up")

    assert result == "second reply"
    assert client.calls == [
        (
            [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "first question"},
                {"role": "assistant", "content": "first answer"},
                {"role": "user", "content": "follow up"},
            ],
            "regular_reply",
        )
    ]
    assert await store.read(1) == [
        {"role": "user", "content": "first question"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "follow up"},
        {"role": "assistant", "content": "second reply"},
    ]
    assert await store.read(2) == [
        {"role": "user", "content": "other user question"},
        {"role": "assistant", "content": "other user answer"},
    ]


@pytest.mark.asyncio
async def test_chat_service_trims_oldest_messages_by_count(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize", encoding="utf-8")
    client = StubOllamaClient(reply="trimmed reply")
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        max_history_messages=3,
    )

    await service.handle_user_message(1, "u3")

    assert client.calls == [
        (
            [
                {"role": "system", "content": "You are helpful"},
                {"role": "user", "content": "u2"},
                {"role": "assistant", "content": "a2"},
                {"role": "user", "content": "u3"},
            ],
            "regular_reply",
        )
    ]


@pytest.mark.asyncio
async def test_chat_service_preserves_order_after_trimming(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize", encoding="utf-8")
    client = StubOllamaClient(reply="ordered")
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "user", "content": "first"},
            {"role": "assistant", "content": "second"},
            {"role": "user", "content": "third"},
            {"role": "assistant", "content": "fourth"},
            {"role": "user", "content": "fifth"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        max_history_messages=4,
    )

    await service.handle_user_message(1, "sixth")

    assert client.calls[0][0] == [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "third"},
        {"role": "assistant", "content": "fourth"},
        {"role": "user", "content": "fifth"},
        {"role": "user", "content": "sixth"},
    ]


@pytest.mark.asyncio
async def test_chat_service_keeps_current_user_message_when_char_limit_is_small(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize", encoding="utf-8")
    client = StubOllamaClient(reply="char limited")
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "user", "content": "old-user"},
            {"role": "assistant", "content": "old-assistant"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        max_history_messages=10,
        max_context_chars=len("current-question"),
    )

    await service.handle_user_message(1, "current-question")

    assert client.calls[0][0] == [
        {"role": "system", "content": "You are helpful"},
        {"role": "user", "content": "current-question"},
    ]


@pytest.mark.asyncio
async def test_chat_service_keeps_summary_before_recent_tail(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize", encoding="utf-8")
    client = StubOllamaClient(reply="summary kept")
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "summary", "content": "older dialog"},
            {"role": "user", "content": "recent user"},
            {"role": "assistant", "content": "recent answer"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        max_history_messages=3,
        max_context_chars=4000,
    )

    await service.handle_user_message(1, "new question")

    assert client.calls[0][0] == [
        {"role": "system", "content": "You are helpful"},
        {"role": "summary", "content": "older dialog"},
        {"role": "assistant", "content": "recent answer"},
        {"role": "user", "content": "new question"},
    ]


@pytest.mark.asyncio
async def test_chat_service_runs_summary_branch_before_regular_reply(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize older messages", encoding="utf-8")
    client = StubOllamaClient(replies=["compressed context", "final reply"])
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "u3"},
            {"role": "assistant", "content": "a3"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        max_history_messages=8,
        summary_trigger_messages=5,
    )

    result = await service.handle_user_message(1, "u4")

    assert result == "final reply"
    assert client.calls == [
        (
            [
                {"role": "system", "content": "Summarize older messages"},
                {"role": "user", "content": "u1"},
                {"role": "assistant", "content": "a1"},
                {"role": "user", "content": "u2"},
            ],
            "summary_generation",
        ),
        (
            [
                {"role": "system", "content": "You are helpful"},
                {"role": "summary", "content": "compressed context"},
                {"role": "assistant", "content": "a2"},
                {"role": "user", "content": "u3"},
                {"role": "assistant", "content": "a3"},
                {"role": "user", "content": "u4"},
            ],
            "regular_reply",
        ),
    ]


@pytest.mark.asyncio
async def test_chat_service_replaces_old_history_with_summary_message(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize older messages", encoding="utf-8")
    client = StubOllamaClient(replies=["summary text", "assistant reply"])
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "u3"},
            {"role": "assistant", "content": "a3"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        max_history_messages=8,
        summary_trigger_messages=5,
    )

    await service.handle_user_message(1, "u4")

    assert await store.read(1) == [
        {"role": "summary", "content": "summary text"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "u3"},
        {"role": "assistant", "content": "a3"},
        {"role": "user", "content": "u4"},
        {"role": "assistant", "content": "assistant reply"},
    ]


@pytest.mark.asyncio
async def test_chat_service_reuses_existing_summary_in_later_requests(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize older messages", encoding="utf-8")
    client = StubOllamaClient(replies=["follow-up reply"])
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "summary", "content": "older facts"},
            {"role": "assistant", "content": "recent a1"},
            {"role": "user", "content": "recent u2"},
            {"role": "assistant", "content": "recent a2"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        max_history_messages=8,
        summary_trigger_messages=5,
    )

    await service.handle_user_message(1, "fresh question")

    assert client.calls == [
        (
            [
                {"role": "system", "content": "You are helpful"},
                {"role": "summary", "content": "older facts"},
                {"role": "assistant", "content": "recent a1"},
                {"role": "user", "content": "recent u2"},
                {"role": "assistant", "content": "recent a2"},
                {"role": "user", "content": "fresh question"},
            ],
            "regular_reply",
        )
    ]


@pytest.mark.asyncio
async def test_chat_service_does_not_trigger_summary_again_without_enough_new_messages(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize older messages", encoding="utf-8")
    client = StubOllamaClient(reply="reply")
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "summary", "content": "older facts"},
            {"role": "user", "content": "recent u1"},
            {"role": "assistant", "content": "recent a1"},
            {"role": "user", "content": "recent u2"},
            {"role": "assistant", "content": "recent a2"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        max_history_messages=8,
        summary_trigger_messages=5,
    )

    await service.handle_user_message(1, "fresh question")

    assert client.calls == [
        (
            [
                {"role": "system", "content": "You are helpful"},
                {"role": "summary", "content": "older facts"},
                {"role": "user", "content": "recent u1"},
                {"role": "assistant", "content": "recent a1"},
                {"role": "user", "content": "recent u2"},
                {"role": "assistant", "content": "recent a2"},
                {"role": "user", "content": "fresh question"},
            ],
            "regular_reply",
        )
    ]


@pytest.mark.asyncio
async def test_chat_service_truncates_and_normalizes_summary_text(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize older messages", encoding="utf-8")
    client = StubOllamaClient(
        replies=["  first line\n second line   third line  ", "assistant reply"]
    )
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "u3"},
            {"role": "assistant", "content": "a3"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        summary_trigger_messages=5,
        summary_max_chars=12,
    )

    await service.handle_user_message(1, "u4")

    assert await store.read(1) == [
        {"role": "summary", "content": "first line..."},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "u3"},
        {"role": "assistant", "content": "a3"},
        {"role": "user", "content": "u4"},
        {"role": "assistant", "content": "assistant reply"},
    ]


@pytest.mark.asyncio
async def test_chat_service_runs_summary_per_user_without_touching_other_histories(
    tmp_path: Path,
) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("You are helpful", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summarize older messages", encoding="utf-8")
    client = StubOllamaClient(replies=["summary text", "assistant reply"])
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "u3"},
            {"role": "assistant", "content": "a3"},
        ],
    )
    await store.append_many(
        2,
        [
            {"role": "user", "content": "other u1"},
            {"role": "assistant", "content": "other a1"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        summary_trigger_messages=5,
    )

    await service.handle_user_message(1, "u4")

    assert await store.read(1) == [
        {"role": "summary", "content": "summary text"},
        {"role": "assistant", "content": "a2"},
        {"role": "user", "content": "u3"},
        {"role": "assistant", "content": "a3"},
        {"role": "user", "content": "u4"},
        {"role": "assistant", "content": "assistant reply"},
    ]
    assert await store.read(2) == [
        {"role": "user", "content": "other u1"},
        {"role": "assistant", "content": "other a1"},
    ]


@pytest.mark.asyncio
async def test_chat_service_places_system_prompt_first_in_runtime_context(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("Primary system prompt", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summary system prompt", encoding="utf-8")
    client = StubOllamaClient(reply="reply")
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "summary", "content": "older facts"},
            {"role": "assistant", "content": "recent answer"},
        ],
    )
    service = create_service(client, prompt_path, summary_prompt_path, store)

    await service.handle_user_message(1, "new question")

    assert client.calls[0][0][0] == {"role": "system", "content": "Primary system prompt"}


@pytest.mark.asyncio
async def test_chat_service_uses_separate_prompt_for_summary_contract(tmp_path: Path) -> None:
    prompt_path = tmp_path / "system_prompt.txt"
    prompt_path.write_text("Primary system prompt", encoding="utf-8")
    summary_prompt_path = tmp_path / "summarization_prompt.txt"
    summary_prompt_path.write_text("Summary system prompt", encoding="utf-8")
    client = StubOllamaClient(replies=["summary", "reply"])
    store = InMemoryConversationStore()
    await store.append_many(
        1,
        [
            {"role": "user", "content": "u1"},
            {"role": "assistant", "content": "a1"},
            {"role": "user", "content": "u2"},
            {"role": "assistant", "content": "a2"},
            {"role": "user", "content": "u3"},
            {"role": "assistant", "content": "a3"},
        ],
    )
    service = create_service(
        client,
        prompt_path,
        summary_prompt_path,
        store,
        summary_trigger_messages=5,
    )

    await service.handle_user_message(1, "u4")

    assert client.calls[0][0][0] == {"role": "system", "content": "Summary system prompt"}
    assert client.calls[1][0][0] == {"role": "system", "content": "Primary system prompt"}
