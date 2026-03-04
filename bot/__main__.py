from __future__ import annotations

import logging

import discord
from discord.ext import commands

from bot.config import load_config


logger = logging.getLogger("mrc_bot")


class MrcBot(commands.Bot):
    def __init__(self, *, dev_guild_id: int | None) -> None:
        intents = discord.Intents.default()
        super().__init__(command_prefix="!", intents=intents)
        self.dev_guild_id = dev_guild_id

    async def setup_hook(self) -> None:
        await self.load_extension("bot.cogs.image_dimensions")
        await self.load_extension("bot.cogs.get_stats")

        cmds = list(self.tree.get_commands())
        logger.info("Registered %d app command(s):", len(cmds))
        for c in cmds:
            # ContextMenu has `.type`; slash commands don't.
            ctype = getattr(c, "type", None)
            logger.info("- %s (type=%s)", c.name, ctype)

        if self.dev_guild_id is not None:
            guild = discord.Object(id=self.dev_guild_id)
            self.tree.copy_global_to(guild=guild)

            synced = await self.tree.sync(guild=guild)
            logger.info(
                "Synced %d command(s) to dev guild id=%s",
                len(synced),
                self.dev_guild_id,
            )

        synced_global = await self.tree.sync()
        logger.info("Synced %d command(s) globally", len(synced_global))

    async def on_ready(self) -> None:
        logger.info(
            "Logged in as %s (%s)", self.user, self.user.id if self.user else "?"
        )
        logger.info("Connected guilds: %d", len(self.guilds))


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
