#!/usr/bin/env bash
# Install the bot as a systemd service on Ubuntu. Safe to re-run to update.
#
#   sudo deploy/install.sh
#   deploy/install.sh --dry-run     print every step without touching the system
set -euo pipefail

APP_NAME="${APP_NAME:-assistant-bot}"
APP_USER="${APP_USER:-assistant}"
APP_DIR="${APP_DIR:-/opt/$APP_NAME}"
ENV_DIR="${ENV_DIR:-/etc/$APP_NAME}"
ENV_FILE="$ENV_DIR/env"
UNIT_FILE="/etc/systemd/system/$APP_NAME.service"

SRC_DIR="$(dirname "$(dirname "$(readlink -f "$0")")")"
DRY_RUN=false
[[ "${1:-}" == "--dry-run" ]] && DRY_RUN=true

die() { printf 'error: %s\n' "$1" >&2; exit 1; }
step() { printf '\n==> %s\n' "$1"; }
note() { printf '    %s\n' "$1"; }

# In dry-run mode privileged commands are printed instead of executed.
run() {
    if [[ "$DRY_RUN" == true ]]; then
        printf '    would run: %s\n' "$*"
    else
        "$@"
    fi
}

[[ "$DRY_RUN" == true || "$EUID" -eq 0 ]] || die "run as root: sudo $0"
[[ -f "$SRC_DIR/requirements.txt" ]] || die "cannot find the project at $SRC_DIR"

step "Installing prerequisites"
run apt-get update -qq
run apt-get install -y -qq python3 python3-venv python3-pip rsync

step "Creating the service account"
if id "$APP_USER" &>/dev/null; then
    note "user $APP_USER already exists"
else
    note "creating system user $APP_USER"
    # No home directory and no shell: this account exists only to run the bot.
    run useradd --system --no-create-home --shell /usr/sbin/nologin "$APP_USER"
fi

step "Copying the project to $APP_DIR"
run mkdir -p "$APP_DIR/data"
# .env and .venv are deliberately excluded: secrets live in $ENV_FILE and the
# virtualenv is rebuilt on the target machine.
run rsync -a --delete \
    --exclude '.git' --exclude '.venv' --exclude '.env' \
    --exclude 'data' --exclude '__pycache__' \
    "$SRC_DIR/" "$APP_DIR/"
run chown -R "$APP_USER:$APP_USER" "$APP_DIR"

step "Building the virtualenv"
run runuser -u "$APP_USER" -- python3 -m venv "$APP_DIR/.venv"
run runuser -u "$APP_USER" -- "$APP_DIR/.venv/bin/pip" install --quiet --upgrade pip
run runuser -u "$APP_USER" -- "$APP_DIR/.venv/bin/pip" install --quiet -r "$APP_DIR/requirements.txt"

step "Preparing the secrets file"
run mkdir -p "$ENV_DIR"
if [[ -f "$ENV_FILE" ]]; then
    note "$ENV_FILE already exists, leaving it untouched"
else
    note "creating $ENV_FILE from .env.example"
    run install -m 600 -o root -g root "$SRC_DIR/.env.example" "$ENV_FILE"
fi
# Root-owned and unreadable to anyone else, including the account running the bot.
run chown root:root "$ENV_DIR" "$ENV_FILE"
run chmod 700 "$ENV_DIR"
run chmod 600 "$ENV_FILE"

step "Installing the systemd unit"
run install -m 644 "$SRC_DIR/deploy/$APP_NAME.service" "$UNIT_FILE"
run systemctl daemon-reload
run systemctl enable "$APP_NAME"

step "Done"
if [[ "$DRY_RUN" == false ]] && ! grep -qE '^DISCORD_TOKEN=.+' "$ENV_FILE"; then
    note "Next: put your token and provider key in $ENV_FILE"
    note "      sudo nano $ENV_FILE"
    note "Then: sudo systemctl start $APP_NAME"
else
    note "Start:  sudo systemctl start $APP_NAME"
    note "Status: systemctl status $APP_NAME"
    note "Logs:   journalctl -u $APP_NAME -f"
fi
