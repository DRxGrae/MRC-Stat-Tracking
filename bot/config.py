from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


@dataclass(frozen=True)
class Config:
    token: str
    dev_guild_id: int | None


def load_config() -> Config:
    # Local dev convenience: load variables from a repo-root `.env` if present.
    # DigitalOcean/App Platform env vars still work normally and take precedence.
    repo_root = Path(__file__).resolve().parents[1]
    load_dotenv(dotenv_path=repo_root / ".env", override=False)

    token = os.getenv("DISCORD_TOKEN", "").strip()
    if not token:
        raise RuntimeError("DISCORD_TOKEN is required")

    raw_guild_id = os.getenv("DISCORD_GUILD_ID", "").strip()
    dev_guild_id = int(raw_guild_id) if raw_guild_id else None

    return Config(token=token, dev_guild_id=dev_guild_id)
