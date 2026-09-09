"""Provider registry: picks the assistant implementation from the config."""

from __future__ import annotations

from bot.ai.base import Assistant, AssistantError
from bot.ai.deepseek import DeepSeekAssistant
from bot.ai.gemini import GeminiAssistant
from bot.ai import deepseek, gemini

# Order decides how providers are listed on the /setup screen.
PROVIDERS: dict[str, tuple[type[Assistant], str]] = {
    "deepseek": (DeepSeekAssistant, deepseek.DEFAULT_MODEL),
    "gemini": (GeminiAssistant, gemini.DEFAULT_MODEL),
}


def default_model(provider: str) -> str:
    return PROVIDERS[provider][1]


def create_assistant(provider: str, api_key: str, model: str) -> Assistant:
    assistant_cls, _ = PROVIDERS[provider]
    return assistant_cls(api_key=api_key, model=model)


__all__ = ["Assistant", "AssistantError", "PROVIDERS", "create_assistant", "default_model"]
