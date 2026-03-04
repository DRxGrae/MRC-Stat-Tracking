from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

import numpy as np


@dataclass(frozen=True)
class PlayerRow:
    name: str
    goal: int
    assist: int
    passes: int
    interception: int
    save: int
    score: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class OCRResult:
    texts: list[str]
    boxes: list[np.ndarray]

    def to_dict(self) -> dict[str, Any]:
        return {
            "texts": list(self.texts),
            "boxes": [list(map(int, box)) for box in self.boxes],
        }


@dataclass(frozen=True)
class OCRParsedResult:
    home: list[PlayerRow]
    away: list[PlayerRow]
