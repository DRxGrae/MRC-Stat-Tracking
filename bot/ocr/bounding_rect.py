from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class BoundingRect:
    x1: int
    y1: int
    x2: int
    y2: int

    @classmethod
    def from_ndarray(cls, box: np.ndarray) -> "BoundingRect":
        if box is None:
            raise ValueError("Box is None")
        if len(box) != 4:
            raise ValueError(f"Invalid box (expected len=4): {box}")
        x1, y1, x2, y2 = box[0], box[1], box[2], box[3]
        return cls(int(x1), int(y1), int(x2), int(y2))

    @property
    def top_edge(self) -> int:
        return self.y1

    @property
    def left_edge(self) -> int:
        return self.x1

    @property
    def right_edge(self) -> int:
        return self.x2

    @property
    def bottom_edge(self) -> int:
        return self.y2

    @property
    def top_left(self) -> tuple[int, int]:
        return (self.x1, self.y1)

    @property
    def bottom_right(self) -> tuple[int, int]:
        return (self.x2, self.y2)

    @property
    def center(self) -> tuple[int, int]:
        return (int((self.x1 + self.x2) / 2), int((self.y1 + self.y2) / 2))

    def to_dict(self) -> dict[str, int]:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}
