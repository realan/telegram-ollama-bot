from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет. Я локальный AI-ассистент на базе Ollama.\n\n"
        "Отправь любое текстовое сообщение — отвечу с учётом истории нашего диалога.\n"
        "Команда /clear сбросит историю, если хочешь начать заново.\n\n"
        "/help — полный список команд."
    )

