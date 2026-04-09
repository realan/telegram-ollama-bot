from __future__ import annotations

import logging

from aiogram import F, Router
from aiogram.types import Message

from app.services.chat_service import ChatService
from app.utils.exceptions import (
    ModelNotFoundError,
    OllamaTimeoutError,
    OllamaUnavailableError,
    ValidationError,
)
from app.utils.telegram_text import split_text


logger = logging.getLogger(__name__)
router = Router()

OLLAMA_UNAVAILABLE_MESSAGE = (
    "Локальная модель сейчас недоступна. Проверь запуск Ollama и попробуй снова."
)
MODEL_NOT_FOUND_MESSAGE = (
    "Указанная модель не найдена в Ollama. Проверь конфигурацию."
)
TIMEOUT_MESSAGE = "Модель отвечает слишком долго. Попробуй еще раз."
GENERIC_ERROR_MESSAGE = "Произошла ошибка при обработке сообщения."
EMPTY_TEXT_MESSAGE = "Отправь непустое текстовое сообщение."
UNSUPPORTED_INPUT_MESSAGE = "В этом MVP я обрабатываю только текстовые сообщения."


@router.message(F.text)
async def chat_handler(message: Message, chat_service: ChatService) -> None:
    logger.info(
        "incoming text message metadata",
        extra={"chat_id": message.chat.id, "user_id": message.from_user.id if message.from_user else None},
    )

    try:
        reply = await chat_service.handle_user_message(message.text or "")
    except ValidationError:
        await message.answer(EMPTY_TEXT_MESSAGE)
        return
    except OllamaUnavailableError:
        await message.answer(OLLAMA_UNAVAILABLE_MESSAGE)
        return
    except ModelNotFoundError:
        await message.answer(MODEL_NOT_FOUND_MESSAGE)
        return
    except OllamaTimeoutError:
        await message.answer(TIMEOUT_MESSAGE)
        return
    except Exception:
        logger.exception("telegram message processing failed")
        await message.answer(GENERIC_ERROR_MESSAGE)
        return

    for chunk in split_text(reply):
        try:
            await message.answer(chunk)
        except Exception:
            logger.exception("telegram send failed")
            raise


@router.message()
async def unsupported_message_handler(message: Message) -> None:
    await message.answer(UNSUPPORTED_INPUT_MESSAGE)
