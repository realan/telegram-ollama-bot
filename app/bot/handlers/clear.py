from __future__ import annotations

import logging

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from app.memory import ConversationStore


logger = logging.getLogger(__name__)
router = Router()

CLEAR_CONFIRM_MESSAGE = "История диалога очищена. Начинаем сначала."
CLEAR_ERROR_MESSAGE = "Не удалось очистить историю. Попробуй ещё раз."


@router.message(Command("clear"))
async def clear_handler(message: Message, conversation_store: ConversationStore) -> None:
    user_id = message.from_user.id if message.from_user else None
    if user_id is None:
        logger.error("telegram message has no from_user", extra={"chat_id": message.chat.id})
        await message.answer(CLEAR_ERROR_MESSAGE)
        return

    await conversation_store.clear(user_id)
    logger.info("conversation history cleared", extra={"user_id": user_id})
    await message.answer(CLEAR_CONFIRM_MESSAGE)
