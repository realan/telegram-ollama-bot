from __future__ import annotations

from typing import Literal, TypedDict


MessageRole = Literal["system", "user", "assistant", "summary"]


class Message(TypedDict):
    role: MessageRole
    content: str
