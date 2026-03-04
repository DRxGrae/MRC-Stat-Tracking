from __future__ import annotations

from dataclasses import dataclass

from bot.ocr.bounding_rect import BoundingRect


@dataclass
class Anchors:
    home: BoundingRect | None = None
    away: BoundingRect | None = None
    score: BoundingRect | None = None
    goal: BoundingRect | None = None
    assist: BoundingRect | None = None
    passing: BoundingRect | None = None
    interception: BoundingRect | None = None
    save: BoundingRect | None = None
    home_total: BoundingRect | None = None
    away_total: BoundingRect | None = None

    def all_anchors(self) -> list[BoundingRect | None]:
        return [
            self.home,
            self.away,
            self.score,
            self.goal,
            self.assist,
            self.passing,
            self.interception,
            self.save,
            self.home_total,
            self.away_total,
        ]

    def all_found_count(self) -> int:
        return sum(1 for a in self.all_anchors() if a is not None)

    def has_all_anchors(self) -> bool:
        return self.all_found_count() == len(self.all_anchors())

    @property
    def home_box(self) -> BoundingRect | None:
        if not self.home or not self.home_total or not self.score:
            return None
        return BoundingRect(
            self.home_total.center[0],
            self.home.bottom_edge,
            self.score.right_edge,
            self.home_total.top_edge,
        )

    @property
    def away_box(self) -> BoundingRect | None:
        if not self.away or not self.away_total or not self.score:
            return None
        return BoundingRect(
            self.away_total.center[0],
            self.away.bottom_edge,
            self.score.right_edge,
            self.away_total.top_edge,
        )

    @property
    def home_goal_box(self) -> BoundingRect | None:
        if not self.goal or not self.home_total:
            return None
        return BoundingRect(
            self.goal.left_edge,
            self.goal.top_edge,
            self.goal.right_edge,
            self.home_total.top_edge,
        )

    @property
    def home_assist_box(self) -> BoundingRect | None:
        if not self.assist or not self.home_total:
            return None
        return BoundingRect(
            self.assist.left_edge,
            self.assist.top_edge,
            self.assist.right_edge,
            self.home_total.top_edge,
        )

    @property
    def home_passing_box(self) -> BoundingRect | None:
        if not self.passing or not self.home_total:
            return None
        return BoundingRect(
            self.passing.left_edge,
            self.passing.top_edge,
            self.passing.right_edge,
            self.home_total.top_edge,
        )

    @property
    def home_interception_box(self) -> BoundingRect | None:
        if not self.interception or not self.home_total:
            return None
        return BoundingRect(
            self.interception.left_edge,
            self.interception.top_edge,
            self.interception.right_edge,
            self.home_total.top_edge,
        )

    @property
    def home_save_box(self) -> BoundingRect | None:
        if not self.save or not self.home_total:
            return None
        return BoundingRect(
            self.save.left_edge,
            self.save.top_edge,
            self.save.right_edge,
            self.home_total.top_edge,
        )

    @property
    def home_score_box(self) -> BoundingRect | None:
        if not self.score or not self.home_total:
            return None
        return BoundingRect(
            self.score.left_edge,
            self.score.top_edge,
            self.score.right_edge,
            self.home_total.top_edge,
        )

    @property
    def away_goal_box(self) -> BoundingRect | None:
        if not self.goal or not self.away or not self.away_total:
            return None
        return BoundingRect(
            self.goal.left_edge,
            self.away.bottom_edge,
            self.goal.right_edge,
            self.away_total.top_edge,
        )

    @property
    def away_assist_box(self) -> BoundingRect | None:
        if not self.assist or not self.away or not self.away_total:
            return None
        return BoundingRect(
            self.assist.left_edge,
            self.away.bottom_edge,
            self.assist.right_edge,
            self.away_total.top_edge,
        )

    @property
    def away_passing_box(self) -> BoundingRect | None:
        if not self.passing or not self.away or not self.away_total:
            return None
        return BoundingRect(
            self.passing.left_edge,
            self.away.bottom_edge,
            self.passing.right_edge,
            self.away_total.top_edge,
        )

    @property
    def away_interception_box(self) -> BoundingRect | None:
        if not self.interception or not self.away or not self.away_total:
            return None
        return BoundingRect(
            self.interception.left_edge,
            self.away.bottom_edge,
            self.interception.right_edge,
            self.away_total.top_edge,
        )

    @property
    def away_save_box(self) -> BoundingRect | None:
        if not self.save or not self.away or not self.away_total:
            return None
        return BoundingRect(
            self.save.left_edge,
            self.away.bottom_edge,
            self.save.right_edge,
            self.away_total.top_edge,
        )

    @property
    def away_score_box(self) -> BoundingRect | None:
        if not self.score or not self.away or not self.away_total:
            return None
        return BoundingRect(
            self.score.left_edge,
            self.away.bottom_edge,
            self.score.right_edge,
            self.away_total.top_edge,
        )

    def to_dict(self) -> dict[str, object]:
        def maybe(rect: BoundingRect | None):
            return rect.to_dict() if rect else None

        return {
            "home": maybe(self.home),
            "away": maybe(self.away),
            "score": maybe(self.score),
            "goal": maybe(self.goal),
            "assist": maybe(self.assist),
            "passing": maybe(self.passing),
            "interception": maybe(self.interception),
            "save": maybe(self.save),
            "home_total": maybe(self.home_total),
            "away_total": maybe(self.away_total),
            "found": self.all_found_count(),
            "expected": len(self.all_anchors()),
        }
