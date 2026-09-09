"""The /ask command: a private answer based on the linked channel."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot.ai import AssistantError
from bot.client import AssistantBot
from bot.i18n import translate


class Ask(commands.Cog, name="Ask"):
    def __init__(self, bot: AssistantBot) -> None:
        self.bot = bot

    @app_commands.command(name="ask", description="Ask about the rules of this server")
    @app_commands.describe(question="Your question")
    @app_commands.guild_only()
    @app_commands.checks.cooldown(1, 10.0)
    async def ask(self, interaction: discord.Interaction, question: str) -> None:
        guild = interaction.guild
        locale = self.bot.guild_locale(guild.id)
        channel_id = self.bot.guild_settings(guild.id).source_channel_id
        channel = guild.get_channel(channel_id) if channel_id else None

        if channel is None:
            await interaction.response.send_message(
                translate(locale, "ask.not_configured"), ephemeral=True
            )
            return

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            context = await self._read_channel(channel)
        except discord.Forbidden:
            await interaction.followup.send(
                translate(locale, "error.no_history", channel=channel.mention), ephemeral=True
            )
            return

        if not context:
            await interaction.followup.send(
                translate(locale, "ask.channel_empty", channel=channel.mention), ephemeral=True
            )
            return

        assistant = self.bot.assistant_for(self.bot.guild_provider(guild.id))
        try:
            answer = await assistant.ask(
                question=question,
                channel_context=context,
                channel_index=self._channel_index(guild),
                locale=locale,
            )
        except AssistantError as error:
            await interaction.followup.send(
                translate(locale, error.message_key), ephemeral=True
            )
            return

        await interaction.followup.send(answer, ephemeral=True)

    async def _read_channel(self, channel: discord.TextChannel) -> str:
        """Collect the channel history oldest first, so rules read in order."""
        lines: list[str] = []
        async for message in channel.history(
            limit=self.bot.config.context_limit, oldest_first=True
        ):
            content = message.clean_content.strip()
            if content:
                lines.append(content)
            for embed in message.embeds:
                if embed.title:
                    lines.append(embed.title)
                if embed.description:
                    lines.append(embed.description)
                lines.extend(f"{field.name}: {field.value}" for field in embed.fields)
        return "\n\n".join(lines)

    @staticmethod
    def _channel_index(guild: discord.Guild) -> str:
        return "\n".join(
            f"#{channel.name} -> <#{channel.id}>" for channel in guild.text_channels
        )


async def setup(bot: AssistantBot) -> None:
    await bot.add_cog(Ask(bot))
