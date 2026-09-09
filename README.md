# Assistant

A Discord bot that answers questions about your server rules.

Point it at the channel that holds your rules. When a member runs `/ask`, the bot
reads that channel, sends it to an AI provider together with the question, and
replies privately. Nobody else sees the question or the answer.

```
/ask can I post porn here?
→ No, NSFW content is not allowed in this channel.
  Adult content belongs in #18plus.
```

Answers link real channels, so the reader can click straight through to the one
they were pointed at.

## Features

- **Always current.** The rules channel is read at the moment of every question,
  so edits take effect immediately with no restart and no reindexing.
- **Private answers.** Replies are ephemeral, which keeps rule questions out of
  the chat.
- **Two AI providers.** DeepSeek and Google Gemini, switchable per server from
  the settings screen.
- **Two languages.** English and Ukrainian, covering both the interface and the
  language the bot answers in.
- **Per-server settings.** Every guild picks its own channel, provider and
  language.
- **Modular.** Cogs are discovered and loaded automatically, so a new command is
  a new file.

## Requirements

- Python 3.10 or newer
- A Discord application with a bot token
- An API key for DeepSeek or Google Gemini

In the Discord Developer Portal, enable the **Message Content** privileged
intent. Without it the bot reads empty messages. The bot also needs permission to
read the history of the rules channel.

## Installation

```bash
git clone https://github.com/your-name/Assistant-DiscordBot
cd Assistant-DiscordBot

python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

cp .env.example .env
```

Fill in `DISCORD_TOKEN` and at least one provider key, then start the bot:

```bash
./run.sh
```

`run.sh` creates the virtualenv on first use, verifies that `.env` exists and is
readable only by you, and then starts the bot. `python -m bot` works too if you
prefer to manage the environment yourself.

For a server, see [deploy/](deploy/), which installs the bot as a systemd
service and keeps the secrets in a root-owned file outside the project.

## Configuration

The `.env` file holds the values the bot needs to start. Everything a server
owner can change lives in `/setup` instead.

| Variable | Description |
| --- | --- |
| `DISCORD_TOKEN` | Bot token from the Discord Developer Portal. Required. |
| `DEEPSEEK_API_KEY` | Key from platform.deepseek.com. |
| `GEMINI_API_KEY` | Key from aistudio.google.com. |
| `AI_PROVIDER` | Provider used until a server picks its own. Default `deepseek`. |
| `BOT_LANGUAGE` | Language used until a server picks its own. Default `uk`. |
| `DEEPSEEK_MODEL` | Model override. Default `deepseek-chat`. |
| `GEMINI_MODEL` | Model override. Default `gemini-3.5-flash`. |
| `CONTEXT_LIMIT` | How many recent messages of the rules channel to read. Default 100. |
| `GUILD_ID` | Test guild for instant slash command sync. Development only. |

At least one provider key is required. Both providers appear in `/setup`, but one
without a key cannot be selected.

### Choosing a provider

| Provider | Default model | Typical latency | Notes |
| --- | --- | --- | --- |
| DeepSeek | `deepseek-chat` | ~2s | Paid, no free tier |
| Gemini | `gemini-3.5-flash` | ~15s | Free tier allows 20 requests per minute per model |

`gemini-3.8-flash` is considerably faster than the default, but its free quota is
only 20 requests in total, which a busy server exhausts within minutes.

## Commands

| Command | Who can use it | What it does |
| --- | --- | --- |
| `/setup` | Manage Server permission | Opens the settings screen |
| `/ask <question>` | Everyone | Answers privately from the rules channel |

`/ask` is rate limited to one question per user every 10 seconds.

## Settings screen

`/setup` opens an embed showing what the bot does, its version, the current
settings and a link to this repository. Three buttons sit below it:

| Button | Setting |
| --- | --- |
| 📌 Rules channel | The channel the answers are based on |
| 🧠 AI provider | DeepSeek or Gemini |
| 🌐 Bot language | English or Ukrainian |

Each button swaps in a dropdown while the embed stays in place. Picking a value
saves it and returns to the main screen with the new value shown. The screen is
ephemeral, so it is visible only to the person who opened it.

Settings are stored per guild in `data/settings.json`.

## Project layout

```
bot/
  __main__.py       entry point (python -m bot)
  __init__.py       version and repository link
  config.py         environment settings
  i18n.py           interface strings per language
  client.py         bot class, cog autoloading, provider pool
  storage.py        per-guild settings
  ai/
    base.py         shared prompt, error mapping, provider contract
    deepseek.py     DeepSeek provider
    gemini.py       Google Gemini provider
    __init__.py     provider registry
  cogs/
    setup.py        /setup screen and its pickers
    ask.py          /ask
    events.py       slash command error handling
```

## Extending

### Adding a command

Drop a file into `bot/cogs/` with a `setup` function. It is loaded on the next
start, no registration needed.

```python
from discord import app_commands
from discord.ext import commands


class Example(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="example", description="An example")
    async def example(self, interaction) -> None:
        await interaction.response.send_message("Hello", ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Example(bot))
```

### Adding a language

Add the code to `LANGUAGES` and a full set of strings to `_STRINGS` in
`bot/i18n.py`. The language appears in the settings dropdown automatically.

### Adding an AI provider

Subclass `Assistant` from `bot/ai/base.py`, implement `ask`, and register the
class in `PROVIDERS` in `bot/ai/__init__.py`. Its key and model are read from
`<PROVIDER>_API_KEY` and `<PROVIDER>_MODEL` without further wiring.

## Notes

The full rules channel is sent with every question, so input token cost scales
with the number of questions rather than being paid once. Only the most recent
`CONTEXT_LIMIT` messages are included; older ones fall outside the context.

Never commit `.env`. It is listed in `.gitignore`, and the token and API keys are
kept out of the config object's `repr` so they cannot surface in a traceback.
