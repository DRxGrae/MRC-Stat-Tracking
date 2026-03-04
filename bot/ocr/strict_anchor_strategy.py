from __future__ import annotations

from bot.ocr.bounding_rect import BoundingRect
from bot.ocr.ocr_result import OCRParsedResult, PlayerRow
from bot.ocr.strategies import AnchorBasedStrategy


class StrictAnchorStrategy(AnchorBasedStrategy):
    strict = True

    def parse_players(
        self,
        grouped_rows: list[list[tuple[str, BoundingRect]]],
        goal_box: BoundingRect,
        assist_box: BoundingRect,
        passing_box: BoundingRect,
        interception_box: BoundingRect,
        save_box: BoundingRect,
        score_box: BoundingRect,
    ) -> list[PlayerRow]:
        players: list[PlayerRow] = []

        for row in grouped_rows:
            name = ""
            goal = None
            assist = None
            passes = None
            interception = None
            save = None
            score = None

            for text, box in row:
                center_x, center_y = box.center
                if self.in_bounds(goal_box, center_x, center_y) and text.isnumeric():
                    goal = int(text)
                elif (
                    self.in_bounds(assist_box, center_x, center_y) and text.isnumeric()
                ):
                    assist = int(text)
                elif (
                    self.in_bounds(passing_box, center_x, center_y) and text.isnumeric()
                ):
                    passes = int(text)
                elif (
                    self.in_bounds(interception_box, center_x, center_y)
                    and text.isnumeric()
                ):
                    interception = int(text)
                elif self.in_bounds(save_box, center_x, center_y) and text.isnumeric():
                    save = int(text)
                elif self.in_bounds(score_box, center_x, center_y) and text.isnumeric():
                    score = int(text)
                else:
                    name += text + " "

            missing_stats = []
            if goal is None:
                missing_stats.append("goal")
            if assist is None:
                missing_stats.append("assist")
            if passes is None:
                missing_stats.append("passes")
            if interception is None:
                missing_stats.append("interception")
            if save is None:
                missing_stats.append("save")
            if score is None:
                missing_stats.append("score")

            if missing_stats:
                self.add_parsing_error(f"Missing stats: {', '.join(missing_stats)}")
                continue

            players.append(
                PlayerRow(
                    " ".join(name.split()),
                    int(goal),
                    int(assist),
                    int(passes),
                    int(interception),
                    int(save),
                    int(score),
                )
            )

        return players

    def parse(self) -> OCRParsedResult:
        if not self.anchors.has_all_anchors():
            self.add_parsing_error("Not all anchors found")
            return OCRParsedResult([], [])

        if not self.anchors.home_box or not self.anchors.away_box:
            self.add_parsing_error("Missing home/away boxes")
            return OCRParsedResult([], [])

        home = self.collect_within_bounds(self.anchors.home_box)
        away = self.collect_within_bounds(self.anchors.away_box)

        home_rows = self.group_into_rows(home)
        away_rows = self.group_into_rows(away)

        home_players = self.parse_players(
            home_rows,
            self.anchors.home_goal_box,
            self.anchors.home_assist_box,
            self.anchors.home_passing_box,
            self.anchors.home_interception_box,
            self.anchors.home_save_box,
            self.anchors.home_score_box,
        )
        away_players = self.parse_players(
            away_rows,
            self.anchors.away_goal_box,
            self.anchors.away_assist_box,
            self.anchors.away_passing_box,
            self.anchors.away_interception_box,
            self.anchors.away_save_box,
            self.anchors.away_score_box,
        )

        return OCRParsedResult(home=home_players, away=away_players)
