"""Interface strings for every language the bot can speak."""

from __future__ import annotations

DEFAULT_LOCALE = "uk"

# Shown in the language picker and used to tell the model which language to answer in.
LANGUAGES: dict[str, tuple[str, str]] = {
    "uk": ("Українська", "Ukrainian"),
    "en": ("English", "English"),
}

_STRINGS: dict[str, dict[str, str]] = {
    "uk": {
        "setup.title": "Налаштування Assistant",
        "setup.description": (
            "Бот відповідає на питання учасників про правила сервера. "
            "Обери канал з правилами, і на команду `/ask` бот даватиме приватну "
            "відповідь на основі того, що в ньому написано."
        ),
        "setup.field.version": "Версія",
        "setup.field.source": "Канал з правилами",
        "setup.field.provider": "Провайдер AI",
        "setup.field.language": "Мова бота",
        "setup.field.links": "Посилання",
        "setup.link.github": "Вихідний код на GitHub",
        "setup.value.unset": "не вибрано",
        "setup.footer": "Налаштування бачиш лише ти.",
        "button.source": "Канал з правилами",
        "button.provider": "Провайдер AI",
        "button.language": "Мова бота",
        "button.back": "Назад",
        "select.source": "Обери канал з правилами",
        "select.provider": "Обери провайдера AI",
        "select.language": "Обери мову бота",
        "provider.unavailable": "ключ не налаштовано",
        "saved.source": "Канал з правилами: {value}",
        "saved.provider": "Провайдер AI: {value}",
        "saved.language": "Мова бота: {value}",
        "error.channel_gone": "Канал недоступний.",
        "error.no_history": (
            "Немає доступу до історії {channel}. Видай право «Читати історію "
            "повідомлень» і спробуй ще раз."
        ),
        "error.provider_unavailable": (
            "Для цього провайдера не задано ключ API. Додай його в .env і перезапусти бота."
        ),
        "ask.not_configured": "Канал не налаштовано. Адміністратор має виконати /setup.",
        "ask.channel_empty": "У {channel} немає повідомлень для аналізу.",
        "ask.refused": "Не можу відповісти на це питання. Звернись до модератора.",
        "ask.empty": "Не вдалося сформувати відповідь. Спробуй переформулювати питання.",
        "ai.error.bad_request": "Модель відхилила запит. Перевір модель і довжину каналу з правилами.",
        "ai.error.auth": "Ключ API недійсний. Це питання до адміністратора бота.",
        "ai.error.forbidden": "Ключ API не має доступу до цієї моделі.",
        "ai.error.not_found": "Обрана модель недоступна. Адміністратору варто оновити модель.",
        "ai.error.rate_limit": "Ліміт запитів до моделі вичерпано. Спробуй пізніше.",
        "ai.error.overloaded": "Модель зараз перевантажена. Спробуй ще раз за хвилину.",
        "ai.error.unknown": "Сервіс відповідей тимчасово недоступний. Спробуй пізніше.",
        "cmd.cooldown": "Зачекай {seconds} с перед наступним запитом.",
        "cmd.forbidden": "Недостатньо прав для цієї команди.",
        "cmd.failed": "Сталася помилка. Спробуй пізніше.",
    },
    "en": {
        "setup.title": "Assistant settings",
        "setup.description": (
            "The bot answers member questions about the server rules. Pick the "
            "channel that holds them and `/ask` will reply privately based on "
            "what is written there."
        ),
        "setup.field.version": "Version",
        "setup.field.source": "Rules channel",
        "setup.field.provider": "AI provider",
        "setup.field.language": "Bot language",
        "setup.field.links": "Links",
        "setup.link.github": "Source code on GitHub",
        "setup.value.unset": "not selected",
        "setup.footer": "Only you can see these settings.",
        "button.source": "Rules channel",
        "button.provider": "AI provider",
        "button.language": "Bot language",
        "button.back": "Back",
        "select.source": "Pick the rules channel",
        "select.provider": "Pick the AI provider",
        "select.language": "Pick the bot language",
        "provider.unavailable": "no API key configured",
        "saved.source": "Rules channel: {value}",
        "saved.provider": "AI provider: {value}",
        "saved.language": "Bot language: {value}",
        "error.channel_gone": "That channel is unavailable.",
        "error.no_history": (
            "No access to the history of {channel}. Grant the Read Message "
            "History permission and try again."
        ),
        "error.provider_unavailable": (
            "No API key is set for this provider. Add it to .env and restart the bot."
        ),
        "ask.not_configured": "No channel is configured yet. An admin has to run /setup.",
        "ask.channel_empty": "{channel} has no messages to work with.",
        "ask.refused": "I cannot answer that. Please ask a moderator.",
        "ask.empty": "I could not produce an answer. Try rephrasing the question.",
        "ai.error.bad_request": "The model rejected the request. Check the model and the size of the rules channel.",
        "ai.error.auth": "The API key is invalid. That is one for the bot administrator.",
        "ai.error.forbidden": "The API key has no access to this model.",
        "ai.error.not_found": "The selected model is unavailable. An admin should update it.",
        "ai.error.rate_limit": "The model request quota is used up. Try again later.",
        "ai.error.overloaded": "The model is overloaded right now. Try again in a minute.",
        "ai.error.unknown": "The answering service is temporarily unavailable. Try again later.",
        "cmd.cooldown": "Wait {seconds}s before the next request.",
        "cmd.forbidden": "You lack the permissions for this command.",
        "cmd.failed": "Something went wrong. Try again later.",
    },
}


def normalize(locale: str | None) -> str:
    return locale if locale in _STRINGS else DEFAULT_LOCALE


def translate(locale: str | None, key: str, **params: object) -> str:
    text = _STRINGS[normalize(locale)].get(key) or _STRINGS[DEFAULT_LOCALE][key]
    return text.format(**params) if params else text


def language_label(locale: str) -> str:
    return LANGUAGES[normalize(locale)][0]


def language_for_prompt(locale: str) -> str:
    return LANGUAGES[normalize(locale)][1]
