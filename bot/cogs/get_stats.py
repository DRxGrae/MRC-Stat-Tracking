from __future__ import annotations

import asyncio
import io
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

IMAGE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
}


def _is_image_attachment(att: discord.Attachment) -> bool:
    if att.content_type and att.content_type.startswith("image/"):
        return True
    return Path(att.filename).suffix.lower() in IMAGE_EXTS


class GetStats(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.ctx_menu = app_commands.ContextMenu(
            name="Get stats",
            callback=self.get_stats_ctx,
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    async def get_stats_ctx(
        self, interaction: discord.Interaction, message: discord.Message
    ) -> None:
        if interaction.guild is None:
            await interaction.response.send_message(
                "This command only works in servers.", ephemeral=True
            )
            return

        if not interaction.user.guild_permissions.administrator:
            await interaction.response.send_message(
                "Admin only (requires Administrator permission).", ephemeral=True
            )
            return

        image_atts = [a for a in message.attachments if _is_image_attachment(a)]
        if not image_atts:
            await interaction.response.send_message(
                "No image attachments found on that message.", ephemeral=True
            )
            return

        att = image_atts[0]

        await interaction.response.defer(ephemeral=True, thinking=True)

        try:
            from bot.app.get_stats import get_stats

            image_bytes = await att.read()
            result = await asyncio.to_thread(get_stats, image_bytes)

            embed = discord.Embed(
                title="Scoreboard OCR",
                description=result.text,
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Home", value=f"```\n{result.embed_home}\n```", inline=False
            )
            embed.add_field(
                name="Away", value=f"```\n{result.embed_away}\n```", inline=False
            )
            embed.set_footer(text=f"Source: {att.filename}")

            file = discord.File(
                fp=io.BytesIO(result.debug_png),
                filename="debug.png",
            )
            embed.set_image(url="attachment://debug.png")

            await interaction.followup.send(embed=embed, file=file, ephemeral=True)

        except Exception as e:  # noqa: BLE001
            await interaction.followup.send(
                f"Failed to OCR image: {type(e).__name__}: {e}", ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GetStats(bot))
