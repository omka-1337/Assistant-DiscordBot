"""DeepSeek provider, reached through its OpenAI-compatible endpoint."""

from __future__ import annotations

import openai
from openai import AsyncOpenAI

from bot.ai.base import Assistant

DEFAULT_MODEL = "deepseek-chat"
BASE_URL = "https://api.deepseek.com"
MAX_OUTPUT_TOKENS = 1024


class DeepSeekAssistant(Assistant):
    def __init__(self, api_key: str, model: str) -> None:
        self._client = AsyncOpenAI(api_key=api_key, base_url=BASE_URL)
        self._model = model

    async def ask(
        self, question: str, channel_context: str, channel_index: str, locale: str
    ) -> str:
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=MAX_OUTPUT_TOKENS,
                temperature=0.2,
                messages=[
                    {
                        "role": "system",
                        "content": self.build_system_prompt(
                            channel_context, channel_index, locale
                        ),
                    },
                    {"role": "user", "content": question},
                ],
            )
        except openai.APIStatusError as error:
            raise self.as_assistant_error(error.status_code, error.message) from error
        except openai.APIError as error:
            raise self.as_assistant_error(None, error) from error

        choice = response.choices[0]
        return self.finalize(choice.message.content, locale, choice.finish_reason)
