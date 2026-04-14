from __future__ import annotations

from collections import defaultdict
from typing import Protocol

from app.memory.types import Message


def _copy_message(message: Message) -> Message:
    return {
        "role": message["role"],
        "content": message["content"],
    }


class ConversationStore(Protocol):
    async def read(self, user_id: int) -> list[Message]: ...

    async def append(self, user_id: int, message: Message) -> None: ...

    async def append_many(self, user_id: int, messages: list[Message]) -> None: ...

    async def replace_after_summary(
        self,
        user_id: int,
        summary_message: Message,
        tail_messages: list[Message],
    ) -> None: ...

    async def clear(self, user_id: int) -> None: ...


class InMemoryConversationStore:
    def __init__(self) -> None:
        self._messages_by_user: defaultdict[int, list[Message]] = defaultdict(list)

    async def read(self, user_id: int) -> list[Message]:
        return [_copy_message(message) for message in self._messages_by_user[user_id]]

    async def append(self, user_id: int, message: Message) -> None:
        self._messages_by_user[user_id].append(_copy_message(message))

    async def append_many(self, user_id: int, messages: list[Message]) -> None:
        self._messages_by_user[user_id].extend(_copy_message(message) for message in messages)

    async def replace_after_summary(
        self,
        user_id: int,
        summary_message: Message,
        tail_messages: list[Message],
    ) -> None:
        self._messages_by_user[user_id] = [
            _copy_message(summary_message),
            *(_copy_message(message) for message in tail_messages),
        ]

    async def clear(self, user_id: int) -> None:
        self._messages_by_user.pop(user_id, None)
