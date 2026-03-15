from __future__ import annotations

import asyncio
import io
from pathlib import Path

import discord
from discord import app_commands
from discord.ext import commands

from bot.app.ocr_client import OcrServiceError, scan_image

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
            image_bytes = await att.read()

            payload, debug_png = await scan_image(
                image_bytes=image_bytes,
                filename=att.filename,
                content_type=att.content_type,
                include_debug=True,
            )

            meta = payload.get("meta") if isinstance(payload.get("meta"), dict) else {}
            home = payload.get("home") if isinstance(payload.get("home"), list) else []
            away = payload.get("away") if isinstance(payload.get("away"), list) else []

            def fmt_team(rows: list[dict]) -> str:
                header = f"{'Player':<18} {'G':>2} {'A':>2} {'P':>2} {'I':>2} {'S':>2} {'Score':>5}"
                lines = [header]
                for r in rows[:5]:
                    name = str(r.get("name") or "")
                    name = " ".join(name.strip().split())
                    if len(name) > 18:
                        name = name[:15] + "..."
                    lines.append(
                        f"{name:<18} {int(r.get('goal') or 0):>2} {int(r.get('assist') or 0):>2} "
                        f"{int(r.get('passes') or 0):>2} {int(r.get('interception') or 0):>2} "
                        f"{int(r.get('save') or 0):>2} {int(r.get('score') or 0):>5}"
                    )
                return "\n".join(lines)

            desc = (
                f"Best strategy: {meta.get('best_strategy') or 'n/a'}"
                f" (score {float(meta.get('best_score') or 0.0):.2f})\n"
                f"Anchors: {int(meta.get('anchors_found') or 0)}/{int(meta.get('anchors_expected') or 0)}"
            )

            embed = discord.Embed(
                title="Scoreboard OCR",
                description=desc,
                color=discord.Color.green(),
            )
            embed.add_field(
                name="Home", value=f"```\n{fmt_team(home)}\n```", inline=False
            )
            embed.add_field(
                name="Away", value=f"```\n{fmt_team(away)}\n```", inline=False
            )
            embed.set_footer(text=f"Source: {att.filename}")

            if debug_png:
                file = discord.File(fp=io.BytesIO(debug_png), filename="debug.png")
                embed.set_image(url="attachment://debug.png")
                await interaction.followup.send(embed=embed, file=file, ephemeral=True)
            else:
                await interaction.followup.send(embed=embed, ephemeral=True)

        except OcrServiceError as e:
            await interaction.followup.send(f"OCR service error: {e}", ephemeral=True)

        except Exception as e:  # noqa: BLE001
            await interaction.followup.send(
                f"Failed to OCR image: {type(e).__name__}: {e}", ephemeral=True
            )


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(GetStats(bot))
