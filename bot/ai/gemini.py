"""Google Gemini provider."""

from __future__ import annotations

import logging

from google import genai
from google.genai import errors, types

from bot.ai.base import Assistant
from bot.i18n import translate

log = logging.getLogger(__name__)

# gemini-3.8-flash is faster but the free tier grants it only 20 requests, which
# a busy server burns through in minutes. 3.5-flash answers in about 15 seconds
# and holds up under repeated calls.
DEFAULT_MODEL = "gemini-3.5-flash"

# Gemini 3.x models think before answering and the reasoning is charged against
# max_output_tokens, so the cap has to leave room for both. Reasoning cannot be
# turned off portably: thinking_budget=0 is rejected by several 3.x models.
MAX_OUTPUT_TOKENS = 2048

# Without explicit retry options the SDK never retries at all. Busy models answer
# 503, and the free tier caps requests per minute per model and asks to come back
# in about eight seconds, so the backoff has to outlast that window. The OpenAI
# client used for DeepSeek retries on its own, so this has no counterpart there.
_RETRY = types.HttpRetryOptions(attempts=4, initial_delay=2.0, max_delay=15.0)


class GeminiAssistant(Assistant):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = genai.Client(
            api_key=api_key, http_options=types.HttpOptions(retry_options=_RETRY)
        )
        self._model = model

    async def ask(
        self, question: str, channel_context: str, channel_index: str, locale: str
    ) -> str:
        config = types.GenerateContentConfig(
            system_instruction=self.build_system_prompt(channel_context, channel_index, locale),
            max_output_tokens=MAX_OUTPUT_TOKENS,
            temperature=0.2,
            # There are no tools, and leaving this on makes the SDK warn per call.
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

        try:
            response = await self._client.aio.models.generate_content(
                model=self._model, contents=question, config=config
            )
        except errors.APIError as error:
            raise self.as_assistant_error(error.code, error.message) from error

        if response.prompt_feedback and response.prompt_feedback.block_reason:
            log.info("Gemini blocked the prompt: %s", response.prompt_feedback.block_reason)
            return translate(locale, "ask.refused")

        candidate = response.candidates[0] if response.candidates else None
        return self.finalize(
            response.text, locale, candidate.finish_reason if candidate else None
        )
