from __future__ import annotations

from pathlib import Path

from app.clients.ollama_client import OllamaClient
from app.memory import ConversationStore, Message
from app.utils.exceptions import ValidationError


class ChatService:
    def __init__(
        self,
        ollama_client: OllamaClient,
        system_prompt_path: Path,
        summarization_prompt_path: Path,
        conversation_store: ConversationStore,
        max_history_messages: int,
        max_context_chars: int,
        summary_trigger_messages: int,
        summary_max_chars: int,
    ) -> None:
        self._ollama_client = ollama_client
        self._system_prompt_path = system_prompt_path
        self._summarization_prompt_path = summarization_prompt_path
        self._conversation_store = conversation_store
        self._max_history_messages = max_history_messages
        self._max_context_chars = max_context_chars
        self._summary_trigger_messages = summary_trigger_messages
        self._summary_max_chars = summary_max_chars

    async def handle_user_message(self, user_id: int, text: str) -> str:
        normalized_text = text.strip()
        if not normalized_text:
            raise ValidationError("Message text must not be empty")

        history = await self._conversation_store.read(user_id)
        history = await self._summarize_history_if_needed(user_id, history)
        user_message: Message = {"role": "user", "content": normalized_text}
        system_prompt = self._load_system_prompt()
        runtime_messages = self._build_runtime_context(
            system_prompt,
            self._trim_history_for_model(
                history,
                user_message,
                reserved_chars=len(system_prompt),
            ),
        )
        reply = await self._ollama_client.generate_reply(
            messages=runtime_messages,
            request_type="regular_reply",
        )
        await self._conversation_store.append_many(
            user_id,
            [
                user_message,
                {"role": "assistant", "content": reply},
            ],
        )
        return reply

    def _load_system_prompt(self) -> str:
        return self._system_prompt_path.read_text(encoding="utf-8").strip()

    def _load_summarization_prompt(self) -> str:
        return self._summarization_prompt_path.read_text(encoding="utf-8").strip()

    async def _summarize_history_if_needed(
        self,
        user_id: int,
        history: list[Message],
    ) -> list[Message]:
        messages_to_summarize, tail_messages = self._split_history_for_summary(history)
        if not messages_to_summarize:
            return history

        summary_text = await self._ollama_client.generate_reply(
            messages=self._build_runtime_context(
                self._load_summarization_prompt(),
                messages_to_summarize,
            ),
            request_type="summary_generation",
        )
        summary_message: Message = {
            "role": "summary",
            "content": self._normalize_summary_text(summary_text),
        }
        await self._conversation_store.replace_after_summary(
            user_id,
            summary_message,
            tail_messages,
        )
        return [summary_message, *tail_messages]

    def _trim_history_for_model(
        self,
        history: list[Message],
        user_message: Message,
        reserved_chars: int = 0,
    ) -> list[Message]:
        trimmed_messages = self._trim_by_message_count([*history, user_message])
        return self._trim_by_total_chars(trimmed_messages, reserved_chars=reserved_chars)

    def _split_history_for_summary(
        self,
        history: list[Message],
    ) -> tuple[list[Message], list[Message]]:
        if not history:
            return [], []

        tail_start = 1 if history[0]["role"] == "summary" else 0
        non_summary_messages = history[tail_start:]
        if len(non_summary_messages) <= self._summary_trigger_messages:
            return [], history

        keep_tail_count = self._summary_keep_tail_messages()
        summary_cutoff = max(len(history) - keep_tail_count, tail_start)
        if summary_cutoff <= 0 or summary_cutoff >= len(history):
            return [], history

        messages_to_summarize = history[:summary_cutoff]
        tail_messages = history[summary_cutoff:]
        return messages_to_summarize, tail_messages

    def _summary_keep_tail_messages(self) -> int:
        return max(self._summary_trigger_messages - 2, 1)

    @staticmethod
    def _build_runtime_context(system_prompt: str, messages: list[Message]) -> list[Message]:
        return [{"role": "system", "content": system_prompt}, *messages]

    def _trim_by_message_count(self, messages: list[Message]) -> list[Message]:
        if len(messages) <= self._max_history_messages:
            return list(messages)

        summary_message = messages[0] if messages and messages[0]["role"] == "summary" else None
        current_user_message = messages[-1]
        recent_history = messages[1:-1] if summary_message else messages[:-1]
        reserved_slots = 1 + int(summary_message is not None)
        tail_limit = max(self._max_history_messages - reserved_slots, 0)
        trimmed_tail = recent_history[-tail_limit:] if tail_limit else []

        trimmed_messages: list[Message] = []
        if summary_message is not None and self._max_history_messages >= 2:
            trimmed_messages.append(summary_message)
        trimmed_messages.extend(trimmed_tail)
        trimmed_messages.append(current_user_message)
        return trimmed_messages

    def _trim_by_total_chars(self, messages: list[Message], reserved_chars: int = 0) -> list[Message]:
        trimmed_messages = list(messages)
        has_summary = bool(trimmed_messages and trimmed_messages[0]["role"] == "summary")

        while self._content_length(trimmed_messages) + reserved_chars > self._max_context_chars:
            if self._has_removable_tail(trimmed_messages, has_summary):
                trimmed_messages.pop(1 if has_summary else 0)
                continue
            if has_summary and len(trimmed_messages) > 1:
                trimmed_messages.pop(0)
                has_summary = False
                continue
            break

        return trimmed_messages

    @staticmethod
    def _content_length(messages: list[Message]) -> int:
        return sum(len(message["content"]) for message in messages)

    @staticmethod
    def _has_removable_tail(messages: list[Message], has_summary: bool) -> bool:
        removable_start = 1 if has_summary else 0
        current_user_index = len(messages) - 1
        return removable_start < current_user_index

    def _normalize_summary_text(self, text: str) -> str:
        normalized_text = " ".join(text.split())
        if len(normalized_text) <= self._summary_max_chars:
            return normalized_text
        truncated_text = normalized_text[: self._summary_max_chars].rstrip()
        return f"{truncated_text}..."
