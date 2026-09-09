"""Slash command error handling."""

from __future__ import annotations

import logging

import discord
from discord import app_commands
from discord.ext import commands

from bot.client import AssistantBot
from bot.i18n import translate

log = logging.getLogger(__name__)


class Events(commands.Cog, name="Events"):
    def __init__(self, bot: AssistantBot) -> None:
        self.bot = bot
        self._previous_handler = bot.tree.on_error

    async def cog_load(self) -> None:
        self.bot.tree.on_error = self.on_app_command_error

    async def cog_unload(self) -> None:
        self.bot.tree.on_error = self._previous_handler

    async def on_app_command_error(
        self, interaction: discord.Interaction, error: app_commands.AppCommandError
    ) -> None:
        locale = self.bot.guild_locale(interaction.guild_id) if interaction.guild_id else None

        if isinstance(error, app_commands.CommandOnCooldown):
            message = translate(locale, "cmd.cooldown", seconds=round(error.retry_after))
        elif isinstance(error, (app_commands.MissingPermissions, app_commands.CheckFailure)):
            message = translate(locale, "cmd.forbidden")
        else:
            log.exception("Error in command %s", interaction.command, exc_info=error)
            message = translate(locale, "cmd.failed")

        await self._reply(interaction, message)

    @staticmethod
    async def _reply(interaction: discord.Interaction, message: str) -> None:
        if interaction.response.is_done():
            await interaction.followup.send(message, ephemeral=True)
        else:
            await interaction.response.send_message(message, ephemeral=True)


async def setup(bot: AssistantBot) -> None:
    await bot.add_cog(Events(bot))
