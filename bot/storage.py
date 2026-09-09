"""Per-guild settings persisted to a JSON file."""

from __future__ import annotations

import asyncio
import json
from dataclasses import asdict, dataclass
from pathlib import Path

DEFAULT_PATH = Path("data/settings.json")


@dataclass(frozen=True)
class GuildSettings:
    source_channel_id: int | None = None
    provider: str | None = None
    locale: str | None = None


class SettingsStore:
    def __init__(self, path: Path = DEFAULT_PATH) -> None:
        self._path = path
        self._lock = asyncio.Lock()
        self._guilds: dict[str, GuildSettings] = {}

    def load(self) -> None:
        if not self._path.exists():
            return
        try:
            raw = json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return

        fields = GuildSettings.__dataclass_fields__
        for guild_id, values in raw.items():
            # Unknown keys are dropped so an older file still loads.
            known = {k: v for k, v in values.items() if k in fields}
            self._guilds[guild_id] = GuildSettings(**known)

    def get(self, guild_id: int) -> GuildSettings:
        return self._guilds.get(str(guild_id), GuildSettings())

    async def update(self, guild_id: int, **changes: object) -> GuildSettings:
        async with self._lock:
            current = self.get(guild_id)
            updated = GuildSettings(**{**asdict(current), **changes})
            self._guilds[str(guild_id)] = updated
            await asyncio.to_thread(self._write)
            return updated

    def _write(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            guild_id: {k: v for k, v in asdict(settings).items() if v is not None}
            for guild_id, settings in self._guilds.items()
        }
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        tmp.replace(self._path)
