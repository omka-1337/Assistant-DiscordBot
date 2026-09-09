# Deployment

Tested on Ubuntu. The bot opens no listening port and only makes outbound
connections to Discord and to the AI provider, so it needs no inbound firewall
rule of its own.

## Install

```bash
git clone https://github.com/your-name/Assistant-DiscordBot
cd Assistant-DiscordBot
sudo deploy/install.sh
```

The installer creates a system account, copies the project to
`/opt/assistant-bot`, builds a virtualenv, writes `/etc/assistant-bot/env` from
`.env.example`, and installs the systemd unit. It is safe to re-run.

Add a `--dry-run` flag to print every step without touching the system.

Then fill in the secrets and start the service:

```bash
sudo nano /etc/assistant-bot/env
sudo systemctl start assistant-bot
journalctl -u assistant-bot -f
```

Only two values are required. Everything else has a default:

```
DISCORD_TOKEN=MTIzNDU2Nzg5...
DEEPSEEK_API_KEY=sk-...
```

Write `NAME=value` with no spaces around the `=`. Keep comments on their own
line: systemd treats a comment after a value as part of the value, so a trailing
`# note` silently corrupts the key.

After editing the file, restart the service so the new values are read:

```bash
sudo systemctl restart assistant-bot
```

## Update

```bash
cd Assistant-DiscordBot
git pull
sudo deploy/install.sh
sudo systemctl restart assistant-bot
```

The update replaces the code but keeps `/opt/assistant-bot/data` and the
secrets file untouched.

## How the secrets are protected

Secrets never live next to the code. They sit in `/etc/assistant-bot/env`, owned
by root with mode 600, inside a directory with mode 700.

systemd reads that file as root and hands the values to the process only after
dropping privileges. The `assistant` account that runs the bot cannot open the
file at all. A bug in the bot, or in one of its dependencies, cannot read the
secrets off disk.

The unit also confines the process:

| Setting | Effect |
| --- | --- |
| `User=assistant` | Runs unprivileged, with no home directory and no shell |
| `ProtectSystem=strict` | The whole filesystem is read-only |
| `ReadWritePaths=/opt/assistant-bot/data` | Except the one directory it must write |
| `ProtectHome=true` | Home directories are invisible |
| `RestrictAddressFamilies=AF_INET AF_INET6` | Only IPv4 and IPv6 sockets |
| `NoNewPrivileges=true` | Privileges can never be regained |
| `MemoryDenyWriteExecute=true` | No executing freshly written memory |
| `ProtectProc=invisible` | Other processes are not visible in `/proc` |

`systemd-analyze security assistant-bot` reports an exposure level of 3.8, which
it labels OK.

## What this does not protect against

Environment variables of a running process are readable through
`/proc/<pid>/environ` by the process owner and by root. Anyone who gains the
`assistant` account or root can read the secrets.

That is a property of environment-based configuration in general, not of this
setup. The defence that matters is being able to revoke quickly: know where to
regenerate the bot token in the Discord Developer Portal and the API keys in the
provider consoles.

Two habits matter more than the storage mechanism:

- SSH with keys only, password authentication disabled.
- Keep the machine patched, and run nothing else on it that you do not trust.

## Running without systemd

For a local checkout or a quick trial, `./run.sh` from the project root creates
the virtualenv, checks that `.env` is present and mode 600, and starts the bot.
Use `./run.sh --check` to run the checks without starting anything.
