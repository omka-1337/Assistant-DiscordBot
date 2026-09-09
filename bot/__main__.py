"""Точка входу: python -m bot"""

from __future__ import annotations

import asyncio
import logging

import discord

from bot.client import AssistantBot
from bot.config import Config


def setup_logging() -> None:
    discord.utils.setup_logging(level=logging.INFO, root=True)


async def main() -> None:
    setup_logging()
    config = Config.from_env()
    async with AssistantBot(config) as bot:
        await bot.start(config.token)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
