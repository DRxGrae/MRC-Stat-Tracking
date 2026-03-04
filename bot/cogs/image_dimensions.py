from __future__ import annotations

import io
from pathlib import Path
from typing import Iterable

import discord
from discord import app_commands
from discord.ext import commands
from PIL import Image

IMAGE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".webp",
    ".gif",
    ".bmp",
    ".tif",
    ".tiff",
}


def _is_image_attachment(att: discord.Attachment) -> bool:
    if att.content_type and att.content_type.startswith("image/"):
        return True
    return Path(att.filename).suffix.lower() in IMAGE_EXTS


async def _attachment_dimensions(att: discord.Attachment) -> tuple[int, int]:
    data = await att.read()
    with Image.open(io.BytesIO(data)) as img:
        w, h = img.size
    return w, h


class ImageDimensions(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

        self.ctx_menu = app_commands.ContextMenu(
            name="Image dimensions",
            callback=self.image_dimensions,
        )
        self.bot.tree.add_command(self.ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.ctx_menu.name, type=self.ctx_menu.type)

    async def image_dimensions(
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

        await interaction.response.defer(ephemeral=True, thinking=True)

        atts: Iterable[discord.Attachment] = message.attachments
        image_atts = [a for a in atts if _is_image_attachment(a)]
        if not image_atts:
            await interaction.followup.send(
                "No image attachments found on that message.", ephemeral=True
            )
            return

        lines: list[str] = []
        for att in image_atts:
            try:
                w, h = await _attachment_dimensions(att)
                lines.append(f"{att.filename} - {w}x{h}")
            except Exception as e:  # noqa: BLE001
                lines.append(f"{att.filename} - failed to read ({type(e).__name__})")

        await interaction.followup.send("\n".join(lines), ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ImageDimensions(bot))
