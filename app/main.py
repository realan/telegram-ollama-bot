from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramAPIError

from app.bot.router import create_router
from app.clients.ollama_client import OllamaClient
from app.config import load_settings
from app.logging_config import setup_logging
from app.services.chat_service import ChatService


logger = logging.getLogger(__name__)


async def run() -> None:
    settings = load_settings()
    setup_logging(settings.app_log_level)

    logger.info("startup")

    bot = Bot(
        token=settings.telegram_bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dispatcher = Dispatcher()
    dispatcher.include_router(create_router())

    ollama_client = OllamaClient(
        base_url=settings.ollama_base_url,
        model=settings.ollama_model,
        timeout_seconds=settings.ollama_timeout_seconds,
    )
    dispatcher["chat_service"] = ChatService(
        ollama_client=ollama_client,
        system_prompt_path=settings.system_prompt_path,
    )

    logger.info("bot polling started")
    try:
        await dispatcher.start_polling(bot)
    except TelegramAPIError:
        logger.exception("telegram polling failed")
        raise
    finally:
        await bot.session.close()


def main() -> None:
    asyncio.run(run())


if __name__ == "__main__":
    main()
