from __future__ import annotations

import asyncio
import logging

import discord
from discord.ext import commands

from bot.config import load_config


class MrcBot(commands.Bot):
    def __init__(self, *, dev_guild_id: int | None) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.dev_guild_id = dev_guild_id

    async def setup_hook(self) -> None:
        await self.load_extension("bot.cogs.image_dimensions")

        if self.dev_guild_id is not None:
            guild = discord.Object(id=self.dev_guild_id)
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)

        await self.tree.sync()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    cfg = load_config()
    bot = MrcBot(dev_guild_id=cfg.dev_guild_id)
    bot.run(cfg.token)


if __name__ == "__main__":
    main()
