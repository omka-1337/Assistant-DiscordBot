#!/usr/bin/env bash
# Start the bot from a local checkout. For a server, use deploy/install.sh instead.
#
#   ./run.sh          create the venv if needed, then start the bot
#   ./run.sh --check   run every pre-flight check and exit without starting
set -euo pipefail

cd "$(dirname "$(readlink -f "$0")")"

VENV=".venv"
PYTHON="${PYTHON:-python3}"
CHECK_ONLY=false
[[ "${1:-}" == "--check" ]] && CHECK_ONLY=true

die() { printf 'error: %s\n' "$1" >&2; exit 1; }
note() { printf '  %s\n' "$1"; }

# --- interpreter -------------------------------------------------------------
command -v "$PYTHON" >/dev/null || die "$PYTHON not found; install python3"
if ! "$PYTHON" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)'; then
    die "python 3.10 or newer is required, found $("$PYTHON" --version)"
fi
note "interpreter: $("$PYTHON" --version)"

# --- virtualenv --------------------------------------------------------------
if [[ ! -x "$VENV/bin/python" ]]; then
    note "creating $VENV"
    "$PYTHON" -m venv "$VENV" || die "could not create the venv; on Ubuntu: apt install python3-venv"
    "$VENV/bin/pip" install --quiet --upgrade pip
    "$VENV/bin/pip" install --quiet -r requirements.txt
    note "dependencies installed"
else
    note "venv: $VENV"
fi

# --- secrets -----------------------------------------------------------------
[[ -f .env ]] || die "no .env file; copy .env.example to .env and fill it in"

# The file holds a bot token and API keys, so nobody else on the box should read it.
PERMS="$(stat -c '%a' .env)"
if [[ "$PERMS" != "600" ]]; then
    chmod 600 .env
    note ".env permissions tightened from $PERMS to 600"
fi

if ! grep -qE '^DISCORD_TOKEN=.+' .env; then
    die "DISCORD_TOKEN is empty in .env"
fi
if ! grep -qE '^(DEEPSEEK|GEMINI)_API_KEY=.+' .env; then
    die "no provider key in .env; set DEEPSEEK_API_KEY or GEMINI_API_KEY"
fi
note "secrets present, .env is mode 600"

mkdir -p data

if [[ "$CHECK_ONLY" == true ]]; then
    note "checks passed, not starting"
    exit 0
fi

exec "$VENV/bin/python" -m bot
