"""Settings loaded from the environment (.env)."""

from __future__ import annotations

import os
from dataclasses import dataclass, field

from dotenv import load_dotenv

from bot.ai import PROVIDERS, default_model
from bot.i18n import DEFAULT_LOCALE, LANGUAGES

load_dotenv()

DEFAULT_PROVIDER = "deepseek"


@dataclass(frozen=True)
class Config:
    # Secrets are kept out of repr so a stray print or traceback cannot leak them.
    token: str = field(repr=False)
    guild_id: int | None = None
    default_provider: str = DEFAULT_PROVIDER
    default_locale: str = DEFAULT_LOCALE
    api_keys: dict[str, str] = field(repr=False, default_factory=dict)
    models: dict[str, str] = field(default_factory=dict)
    context_limit: int = 100

    def has_key(self, provider: str) -> bool:
        return provider in self.api_keys

    @classmethod
    def from_env(cls) -> "Config":
        token = os.getenv("DISCORD_TOKEN", "").strip()
        if not token:
            raise RuntimeError(
                "DISCORD_TOKEN is not set. Copy .env.example to .env and paste the bot token."
            )

        # Every provider with a key stays selectable from the /setup screen.
        api_keys = {}
        models = {}
        for provider in PROVIDERS:
            key = os.getenv(f"{provider.upper()}_API_KEY", "").strip()
            if key:
                api_keys[provider] = key
            models[provider] = (
                os.getenv(f"{provider.upper()}_MODEL", "").strip() or default_model(provider)
            )

        if not api_keys:
            raise RuntimeError(
                "No provider key found. Set at least one of: "
                + ", ".join(f"{p.upper()}_API_KEY" for p in PROVIDERS)
            )

        default_provider = (os.getenv("AI_PROVIDER", "").strip() or DEFAULT_PROVIDER).lower()
        if default_provider not in PROVIDERS:
            raise RuntimeError(
                f"Unknown AI_PROVIDER '{default_provider}'. Supported: {', '.join(PROVIDERS)}."
            )
        if default_provider not in api_keys:
            default_provider = next(iter(api_keys))

        locale = (os.getenv("BOT_LANGUAGE", "").strip() or DEFAULT_LOCALE).lower()
        if locale not in LANGUAGES:
            raise RuntimeError(
                f"Unknown BOT_LANGUAGE '{locale}'. Supported: {', '.join(LANGUAGES)}."
            )

        raw_guild = os.getenv("GUILD_ID", "").strip()
        raw_limit = os.getenv("CONTEXT_LIMIT", "").strip()

        return cls(
            token=token,
            guild_id=int(raw_guild) if raw_guild.isdigit() else None,
            default_provider=default_provider,
            default_locale=locale,
            api_keys=api_keys,
            models=models,
            context_limit=int(raw_limit) if raw_limit.isdigit() else 100,
        )
