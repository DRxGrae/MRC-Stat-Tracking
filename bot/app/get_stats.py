from __future__ import annotations
import os
import threading
from dataclasses import dataclass
from typing import Any
from typing import TYPE_CHECKING

import cv2
import numpy as np

if TYPE_CHECKING:
    from bot.ocr.engine import OCREngine
    from bot.ocr.ocr_result import OCRParsedResult


_engine_lock = threading.Lock()
_engine: OCREngine | None = None


def _get_engine() -> OCREngine:
    global _engine

    from bot.ocr.engine import OCREngine
    from bot.ocr.lax_anchor_strategy import LaxAnchorStrategy
    from bot.ocr.strict_anchor_strategy import StrictAnchorStrategy

    # Optional: skip PaddleX model host connectivity check (speeds startup, avoids noisy log).
    # PaddleX expects the string "True".
    if os.getenv("PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK") is None:
        os.environ["PADDLE_PDX_DISABLE_MODEL_SOURCE_CHECK"] = "True"

    with _engine_lock:
        if _engine is None:
            _engine = OCREngine(strategies=[StrictAnchorStrategy, LaxAnchorStrategy])
        return _engine


def _encode_png_bytes(img_bgr: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".png", img_bgr)
    if not ok:
        raise RuntimeError("Failed to encode debug image")
    return bytes(buf)


def _format_team_rows(rows: list[dict[str, Any]]) -> str:
    # Name + 6 numeric columns.
    header = f"{'Player':<18} {'G':>2} {'A':>2} {'P':>2} {'I':>2} {'S':>2} {'Score':>5}"
    lines = [header]
    for r in rows:
        name = str(r.get("name") or "")
        name = " ".join(name.strip().split())
        if len(name) > 18:
            name = name[:15] + "..."
        goal = int(r.get("goal") or 0)
        assist = int(r.get("assist") or 0)
        passes = int(r.get("passes") or 0)
        interception = int(r.get("interception") or 0)
        save = int(r.get("save") or 0)
        score = int(r.get("score") or 0)
        lines.append(
            f"{name:<18} {goal:>2} {assist:>2} {passes:>2} {interception:>2} {save:>2} {score:>5}"
        )

    return "\n".join(lines)


def _parsed_to_dict(parsed: OCRParsedResult) -> dict[str, Any]:
    return {
        "home": [p.to_dict() for p in parsed.home],
        "away": [p.to_dict() for p in parsed.away],
    }


def _sum_goals(rows: list[dict[str, Any]]) -> int:
    return sum(int(r.get("goal") or 0) for r in rows)


@dataclass(frozen=True)
class GetStatsResult:
    text: str
    embed_home: str
    embed_away: str
    debug_png: bytes
    meta: dict[str, Any]
    data: dict[str, Any]


def get_stats(image_bytes: bytes) -> GetStatsResult:
    """Run OCR pipeline and return formatted stats + debug overlay.

    This is a synchronous function (CPU-heavy). Call it via asyncio.to_thread.
    """

    engine = _get_engine()

    parsed, anchors, ocr_result, preprocessed_bgr, meta = engine.scan(
        image_bytes,
        min_quality_score=0.0,
        log=None,
    )

    debug_bgr = engine.build_debug_overlay(preprocessed_bgr, anchors, ocr_result)
    debug_png = _encode_png_bytes(debug_bgr)

    data = _parsed_to_dict(parsed)
    home_rows = data["home"]
    away_rows = data["away"]

    home_goals = _sum_goals(home_rows)
    away_goals = _sum_goals(away_rows)

    text = (
        f"Scoreline (from goals column): HOME {home_goals} - {away_goals} AWAY\n"
        f"Best strategy: {meta.get('best_strategy') or 'n/a'}"
        f" (score {float(meta.get('best_score') or 0.0):.2f})\n"
        f"Anchors: {int(meta.get('anchors_found') or 0)}/{int(meta.get('anchors_expected') or 0)}"
    )

    embed_home = _format_team_rows(home_rows)
    embed_away = _format_team_rows(away_rows)

    return GetStatsResult(
        text=text,
        embed_home=embed_home,
        embed_away=embed_away,
        debug_png=debug_png,
        meta=meta,
        data={"home_goals": home_goals, "away_goals": away_goals, **data},
    )
