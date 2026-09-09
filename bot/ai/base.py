"""Shared contract, prompt and error mapping for every AI provider."""

from __future__ import annotations

import abc
import logging

from bot.i18n import language_for_prompt, translate

log = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a Discord server assistant. You answer questions about the \
rules and information published in one specific channel of this server.

Rules for your answers:
- Rely only on the channel content given below. Never invent rules.
- If the content does not cover the question, say so plainly and suggest asking a moderator.
- Always answer in {language}, whatever language the question is written in.
- Be short: two or three sentences, no headings, no markdown lists unless truly needed.
- When you point at another channel, write it as <#CHANNEL_ID> using the channel list \
below so Discord renders a real link.
- Do not mention that you were given a transcript or that you are a language model."""

MAX_DISCORD_MESSAGE = 2000

_STATUS_KEYS = {
    400: "ai.error.bad_request",
    401: "ai.error.auth",
    403: "ai.error.forbidden",
    404: "ai.error.not_found",
    429: "ai.error.rate_limit",
    503: "ai.error.overloaded",
}
_FALLBACK_KEY = "ai.error.unknown"


class AssistantError(RuntimeError):
    """Provider failure carrying the translation key shown to the person asking."""

    def __init__(self, message_key: str) -> None:
        super().__init__(message_key)
        self.message_key = message_key


class Assistant(abc.ABC):
    """Answers a question using the content of the linked channel."""

    @abc.abstractmethod
    async def ask(
        self, question: str, channel_context: str, channel_index: str, locale: str
    ) -> str: ...

    @staticmethod
    def build_system_prompt(channel_context: str, channel_index: str, locale: str) -> str:
        return (
            f"{SYSTEM_PROMPT.format(language=language_for_prompt(locale))}\n\n"
            f"Channels on this server:\n{channel_index}\n\n"
            f"Content of the linked channel:\n{channel_context}"
        )

    @staticmethod
    def finalize(text: str | None, locale: str, finish_reason: object = None) -> str:
        answer = (text or "").strip()
        if answer:
            return answer[:MAX_DISCORD_MESSAGE]
        log.warning("Provider returned no text, finish reason: %s", finish_reason)
        return translate(locale, "ask.empty")

    @staticmethod
    def as_assistant_error(status: int | None, detail: object) -> AssistantError:
        log.error("Provider request failed with status %s: %s", status, detail)
        return AssistantError(_STATUS_KEYS.get(status, _FALLBACK_KEY))
