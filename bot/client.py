"""Bot class: cog autoloading and slash command sync."""

from __future__ import annotations

import logging
import pkgutil

import discord
from discord.ext import commands

from bot import cogs as cogs_package
from bot.ai import Assistant, create_assistant
from bot.config import Config
from bot.i18n import normalize
from bot.storage import GuildSettings, SettingsStore

log = logging.getLogger(__name__)


class AssistantBot(commands.Bot):
    def __init__(self, config: Config) -> None:
        intents = discord.Intents.default()
        intents.message_content = True

        # Slash commands only; the mention prefix keeps commands.Bot happy.
        super().__init__(
            command_prefix=commands.when_mentioned,
            intents=intents,
            help_command=None,
        )
        self.config = config
        self.settings = SettingsStore()
        self._assistants: dict[str, Assistant] = {}

    def guild_provider(self, guild_id: int) -> str:
        """Guild choice wins, but only while its key is still configured."""
        chosen = self.settings.get(guild_id).provider
        if chosen and self.config.has_key(chosen):
            return chosen
        return self.config.default_provider

    def guild_locale(self, guild_id: int) -> str:
        return normalize(self.settings.get(guild_id).locale or self.config.default_locale)

    def guild_settings(self, guild_id: int) -> GuildSettings:
        return self.settings.get(guild_id)

    def assistant_for(self, provider: str) -> Assistant:
        """Clients are built once and reused across every question."""
        if provider not in self._assistants:
            self._assistants[provider] = create_assistant(
                provider, self.config.api_keys[provider], self.config.models[provider]
            )
        return self._assistants[provider]

    async def setup_hook(self) -> None:
        self.settings.load()
        await self.load_cogs()
        await self.sync_commands()

    async def load_cogs(self) -> None:
        """Load every module of the bot.cogs package as an extension."""
        for module in pkgutil.iter_modules(cogs_package.__path__):
            if module.name.startswith("_"):
                continue

            extension = f"{cogs_package.__name__}.{module.name}"
            try:
                await self.load_extension(extension)
            except commands.ExtensionError:
                log.exception("Failed to load %s", extension)
            else:
                log.info("Loaded %s", extension)

    async def sync_commands(self) -> None:
        """Guild sync is instant; a global sync can take up to an hour."""
        if self.config.guild_id is None:
            synced = await self.tree.sync()
            log.info("Synced %d global slash commands", len(synced))
            return

        guild = discord.Object(id=self.config.guild_id)
        self.tree.copy_global_to(guild=guild)
        synced = await self.tree.sync(guild=guild)
        log.info("Synced %d slash commands to guild %s", len(synced), self.config.guild_id)

    async def on_ready(self) -> None:
        log.info("Logged in as %s (ID: %s)", self.user, self.user.id)
        log.info("Guilds: %d", len(self.guilds))
