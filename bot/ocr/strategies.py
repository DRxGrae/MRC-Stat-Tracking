from __future__ import annotations

from abc import ABC

from bot.ocr.anchors import Anchors
from bot.ocr.bounding_rect import BoundingRect
from bot.ocr.ocr_result import OCRParsedResult, OCRResult, PlayerRow


class AnchorBasedStrategy(ABC):
    """Base strategy used to parse OCR tokens into player rows."""

    artifacts = ["*", "\u2605", "\uffe5", "\u6c27", "+"]
    strict = False

    def __init__(
        self,
        ocr_result: OCRResult,
        anchors: Anchors,
        log,
    ) -> None:
        self.texts = ocr_result.texts
        self.boxes = ocr_result.boxes
        self.anchors = anchors
        self.log = log or (lambda *args: None)
        self._parsing_errors = 0

    def add_parsing_error(self, reason: str = "") -> None:
        self._parsing_errors += 1
        if reason:
            self.log(f"Parsing error: {reason}")

    def calculate_quality_score(self, result: OCRParsedResult) -> float:
        score = 1.0
        if self.strict:
            score += 0.1

        home_count = len(result.home)
        away_count = len(result.away)

        if home_count == 0 and away_count == 0:
            return 0.0

        if home_count < 1 or home_count > 5:
            score -= 0.2
        if away_count < 1 or away_count > 5:
            score -= 0.2

        all_players = result.home + result.away
        for player in all_players:
            score -= self._validate_player_stats(player)

        error_penalty = self._parsing_errors * 0.05
        score -= error_penalty
        return max(0.0, min(1.0, score))

    def _validate_player_stats(self, player: PlayerRow) -> float:
        penalty = 0.0

        if not player.name or len(player.name.strip()) < 2:
            penalty += 0.05

        stats = [
            player.goal,
            player.assist,
            player.passes,
            player.interception,
            player.save,
            player.score,
        ]
        for stat in stats:
            if stat < 0:
                penalty += 0.02
            if stat > 100:
                penalty += 0.01

        return penalty

    def in_bounds(self, bounding_box: BoundingRect, x: int, y: int) -> bool:
        return (
            bounding_box.left_edge <= x <= bounding_box.right_edge
            and bounding_box.top_edge <= y <= bounding_box.bottom_edge
        )

    def collect_within_bounds(
        self, bounding_box: BoundingRect
    ) -> list[tuple[str, BoundingRect]]:
        collected: list[tuple[str, BoundingRect]] = []
        for text, box in zip(self.texts, self.boxes):
            rect = BoundingRect.from_ndarray(box)
            center_x, center_y = rect.center
            if (
                self.in_bounds(bounding_box, center_x, center_y)
                and text not in self.artifacts
            ):
                collected.append((text, rect))
        return collected

    def _is_same_row(self, box1: BoundingRect, box2: BoundingRect) -> bool:
        return box1.y1 < box2.y2 and box2.y1 < box1.y2

    def group_into_rows(
        self, items: list[tuple[str, BoundingRect]]
    ) -> list[list[tuple[str, BoundingRect]]]:
        if not items:
            return []

        sorted_items = sorted(items, key=lambda x: x[1].y1)
        rows: list[list[tuple[str, BoundingRect]]] = []
        current_row = [sorted_items[0]]

        for item in sorted_items[1:]:
            if self._is_same_row(current_row[0][1], item[1]):
                current_row.append(item)
            else:
                rows.append(sorted(current_row, key=lambda x: x[1].x1))
                current_row = [item]

        rows.append(sorted(current_row, key=lambda x: x[1].x1))
        return rows

    def parse(self) -> OCRParsedResult:  # pragma: no cover
        raise NotImplementedError
