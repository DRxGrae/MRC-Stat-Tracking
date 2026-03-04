from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass(frozen=True)
class Config:
    token: str
    dev_guild_id: int | None


def load_config() -> Config:
    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN is required")

    raw_guild_id = os.getenv("DISCORD_GUILD_ID", "").strip()
    dev_guild_id = int(raw_guild_id) if raw_guild_id else None

    return Config(token=token, dev_guild_id=dev_guild_id)
