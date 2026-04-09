from __future__ import annotations

from pathlib import Path

from app.clients.ollama_client import OllamaClient
from app.utils.exceptions import ValidationError


class ChatService:
    def __init__(self, ollama_client: OllamaClient, system_prompt_path: Path) -> None:
        self._ollama_client = ollama_client
        self._system_prompt_path = system_prompt_path

    async def handle_user_message(self, text: str) -> str:
        normalized_text = text.strip()
        if not normalized_text:
            raise ValidationError("Message text must not be empty")

        system_prompt = self._load_system_prompt()
        return await self._ollama_client.generate_reply(normalized_text, system_prompt)

    def _load_system_prompt(self) -> str:
        return self._system_prompt_path.read_text(encoding="utf-8").strip()

