from __future__ import annotations

from aiogram import Router

from app.bot.handlers import chat, help, start


def create_router() -> Router:
    router = Router()
    router.include_router(start.router)
    router.include_router(help.router)
    router.include_router(chat.router)
    return router

