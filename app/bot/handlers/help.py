from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message


router = Router()


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    await message.answer(
        "Доступно:\n"
        "/start - приветствие\n"
        "/help - эта справка\n"
        "/clear - очистить историю диалога\n\n"
        "Отправь любое текстовое сообщение — бот ответит с учётом истории диалога."
    )

