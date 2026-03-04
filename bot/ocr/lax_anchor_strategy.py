from __future__ import annotations

from bot.ocr.ocr_result import OCRParsedResult, PlayerRow
from bot.ocr.strategies import AnchorBasedStrategy


class LaxAnchorStrategy(AnchorBasedStrategy):
    def parse_players(
        self, grouped_rows: list[list[tuple[str, object]]]
    ) -> list[PlayerRow]:
        players: list[PlayerRow] = []

        for row in grouped_rows:
            texts = [text for text, _ in row]
            if len(texts) < 6:
                self.add_parsing_error(f"Row has insufficient elements: {len(texts)}")
                continue

            score = texts[-1]
            save = texts[-2]
            interception = texts[-3]
            passes = texts[-4]
            assist = texts[-5]
            goal = texts[-6]
            name = " ".join(texts[:-6])

            if not all(
                v.isnumeric() for v in [goal, assist, passes, interception, save, score]
            ):
                self.add_parsing_error("Non-numeric stats in row")
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
        if not self.anchors.home_box or not self.anchors.away_box:
            self.add_parsing_error("Missing home or away anchor boxes")
            return OCRParsedResult([], [])

        home = self.collect_within_bounds(self.anchors.home_box)
        away = self.collect_within_bounds(self.anchors.away_box)

        home_rows = self.group_into_rows(home)
        away_rows = self.group_into_rows(away)

        home_players = self.parse_players(home_rows)
        away_players = self.parse_players(away_rows)
        return OCRParsedResult(home=home_players, away=away_players)
