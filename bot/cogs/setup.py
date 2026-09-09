"""The /setup screen: one embed with a button per group of settings."""

from __future__ import annotations

import discord
from discord import app_commands
from discord.ext import commands

from bot import GITHUB_URL, __version__
from bot.client import AssistantBot
from bot.i18n import LANGUAGES, language_label, translate

VIEW_TIMEOUT = 300


def build_embed(bot: AssistantBot, guild: discord.Guild, note: str | None = None) -> discord.Embed:
    """The title screen. Every sub-screen keeps it visible above its picker."""
    locale = bot.guild_locale(guild.id)
    settings = bot.guild_settings(guild.id)
    unset = translate(locale, "setup.value.unset")

    channel = guild.get_channel(settings.source_channel_id) if settings.source_channel_id else None
    provider = bot.guild_provider(guild.id)

    embed = discord.Embed(
        title=translate(locale, "setup.title"),
        description=translate(locale, "setup.description"),
        color=discord.Color.blurple(),
    )
    embed.add_field(name=translate(locale, "setup.field.version"), value=__version__)
    embed.add_field(name=translate(locale, "setup.field.provider"), value=provider)
    embed.add_field(name=translate(locale, "setup.field.language"), value=language_label(locale))
    embed.add_field(
        name=translate(locale, "setup.field.source"),
        value=channel.mention if channel else unset,
        inline=False,
    )
    embed.add_field(
        name=translate(locale, "setup.field.links"),
        value=f"[{translate(locale, 'setup.link.github')}]({GITHUB_URL})",
        inline=False,
    )
    if note:
        embed.add_field(name="​", value=f"✅ {note}", inline=False)
    embed.set_footer(text=translate(locale, "setup.footer"))
    return embed


class SetupScreen(discord.ui.View):
    """Root screen. Each button swaps the components, the embed stays put."""

    def __init__(self, bot: AssistantBot, guild: discord.Guild) -> None:
        super().__init__(timeout=VIEW_TIMEOUT)
        self.bot = bot
        self.guild = guild
        locale = bot.guild_locale(guild.id)
        self.source.label = translate(locale, "button.source")
        self.provider.label = translate(locale, "button.provider")
        self.language.label = translate(locale, "button.language")

    async def show(self, interaction: discord.Interaction, note: str | None = None) -> None:
        await interaction.response.edit_message(
            embed=build_embed(self.bot, self.guild, note), view=self
        )

    @discord.ui.button(emoji="📌", style=discord.ButtonStyle.secondary)
    async def source(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await SourceScreen(self.bot, self.guild).show(interaction)

    @discord.ui.button(emoji="🧠", style=discord.ButtonStyle.secondary)
    async def provider(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await ProviderScreen(self.bot, self.guild).show(interaction)

    @discord.ui.button(emoji="🌐", style=discord.ButtonStyle.secondary)
    async def language(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await LanguageScreen(self.bot, self.guild).show(interaction)


class SubScreen(discord.ui.View):
    """A picker plus the button back to the title screen."""

    def __init__(self, bot: AssistantBot, guild: discord.Guild) -> None:
        super().__init__(timeout=VIEW_TIMEOUT)
        self.bot = bot
        self.guild = guild
        self.locale = bot.guild_locale(guild.id)
        self.back.label = translate(self.locale, "button.back")

    async def show(self, interaction: discord.Interaction) -> None:
        await interaction.response.edit_message(
            embed=build_embed(self.bot, self.guild), view=self
        )

    async def done(self, interaction: discord.Interaction, note: str) -> None:
        """Saving returns to the title screen so the new value is visible at once."""
        await SetupScreen(self.bot, self.guild).show(interaction, note)

    @discord.ui.button(emoji="◀", style=discord.ButtonStyle.secondary, row=2)
    async def back(self, interaction: discord.Interaction, _: discord.ui.Button) -> None:
        await SetupScreen(self.bot, self.guild).show(interaction)


class SourceScreen(SubScreen):
    def __init__(self, bot: AssistantBot, guild: discord.Guild) -> None:
        super().__init__(bot, guild)
        self.picker.placeholder = translate(self.locale, "select.source")

    @discord.ui.select(
        cls=discord.ui.ChannelSelect,
        channel_types=[discord.ChannelType.text, discord.ChannelType.news],
        min_values=1,
        max_values=1,
    )
    async def picker(
        self, interaction: discord.Interaction, select: discord.ui.ChannelSelect
    ) -> None:
        channel = self.guild.get_channel(select.values[0].id)
        if channel is None:
            await interaction.response.edit_message(
                content=translate(self.locale, "error.channel_gone"), embed=None, view=None
            )
            return

        if not channel.permissions_for(self.guild.me).read_message_history:
            await interaction.response.edit_message(
                content=translate(self.locale, "error.no_history", channel=channel.mention),
                embed=None,
                view=None,
            )
            return

        await self.bot.settings.update(self.guild.id, source_channel_id=channel.id)
        await self.done(
            interaction, translate(self.locale, "saved.source", value=channel.mention)
        )


class ProviderScreen(SubScreen):
    def __init__(self, bot: AssistantBot, guild: discord.Guild) -> None:
        super().__init__(bot, guild)
        current = bot.guild_provider(guild.id)
        unavailable = translate(self.locale, "provider.unavailable")

        self.picker.placeholder = translate(self.locale, "select.provider")
        self.picker.options = [
            discord.SelectOption(
                label=name,
                value=name,
                description=None if bot.config.has_key(name) else unavailable,
                default=name == current,
            )
            for name in bot.config.models
        ]

    @discord.ui.select(min_values=1, max_values=1)
    async def picker(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ) -> None:
        provider = select.values[0]
        if not self.bot.config.has_key(provider):
            await interaction.response.edit_message(
                content=translate(self.locale, "error.provider_unavailable"),
                embed=None,
                view=None,
            )
            return

        await self.bot.settings.update(self.guild.id, provider=provider)
        await self.done(interaction, translate(self.locale, "saved.provider", value=provider))


class LanguageScreen(SubScreen):
    def __init__(self, bot: AssistantBot, guild: discord.Guild) -> None:
        super().__init__(bot, guild)
        self.picker.placeholder = translate(self.locale, "select.language")
        self.picker.options = [
            discord.SelectOption(label=label, value=code, default=code == self.locale)
            for code, (label, _) in LANGUAGES.items()
        ]

    @discord.ui.select(min_values=1, max_values=1)
    async def picker(
        self, interaction: discord.Interaction, select: discord.ui.Select
    ) -> None:
        locale = select.values[0]
        await self.bot.settings.update(self.guild.id, locale=locale)
        # The note is written in the language that was just picked.
        await self.done(
            interaction, translate(locale, "saved.language", value=language_label(locale))
        )


class Setup(commands.Cog, name="Setup"):
    def __init__(self, bot: AssistantBot) -> None:
        self.bot = bot

    @app_commands.command(name="setup", description="Bot settings")
    @app_commands.guild_only()
    @app_commands.default_permissions(manage_guild=True)
    async def setup(self, interaction: discord.Interaction) -> None:
        guild = interaction.guild
        await interaction.response.send_message(
            embed=build_embed(self.bot, guild),
            view=SetupScreen(self.bot, guild),
            ephemeral=True,
        )


async def setup(bot: AssistantBot) -> None:
    await bot.add_cog(Setup(bot))
