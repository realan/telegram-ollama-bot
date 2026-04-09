from __future__ import annotations

from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Привет. Я отправляю каждое текстовое сообщение в локальную модель через Ollama "
        "и возвращаю ответ без сохранения истории диалога."
    )

