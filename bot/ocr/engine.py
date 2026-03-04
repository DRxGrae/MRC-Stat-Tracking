from __future__ import annotations

import threading
from dataclasses import dataclass
from typing import Any, Callable

import cv2
import numpy as np

from bot.ocr.anchors import Anchors
from bot.ocr.bounding_rect import BoundingRect
from bot.ocr.ocr_result import OCRParsedResult, OCRResult
from bot.ocr.strategies import AnchorBasedStrategy


ANCHOR_TRANSLATIONS = [
    {
        "home": ["home"],
        "away": ["away"],
        "total": ["total", "total match", "totalmatch"],
        "goal": ["goal"],
        "assist": ["assist"],
        "passes": ["pass"],
        "interception": ["interception"],
        "save": ["save"],
        "score": ["score"],
    },
    {
        "home": ["local"],
        "away": ["visitante"],
        "total": ["partido total"],
        "goal": ["gol"],
        "assist": ["asistencia"],
        "passes": ["pases"],
        "interception": ["intercepion", "intercepci\u00f3n"],
        "save": ["parada"],
        "score": ["marcador"],
    },
]


_ocr_lock = threading.Lock()

_paddle_ocr_init_lock = threading.Lock()
_paddle_ocr = None


def _get_paddle_ocr():
    global _paddle_ocr
    if _paddle_ocr is not None:
        return _paddle_ocr
    with _paddle_ocr_init_lock:
        if _paddle_ocr is None:
            from paddleocr import PaddleOCR

            _paddle_ocr = PaddleOCR(
                ocr_version="PP-OCRv5",
                use_doc_orientation_classify=False,
                use_doc_unwarping=False,
                use_textline_orientation=False,
            )
    return _paddle_ocr


@dataclass(frozen=True)
class ScanMeta:
    best_strategy: str
    best_score: float
    min_quality_score: float
    anchors_found: int
    anchors_expected: int

    def to_dict(self) -> dict[str, Any]:
        return {
            "best_strategy": self.best_strategy,
            "best_score": float(self.best_score),
            "min_quality_score": float(self.min_quality_score),
            "anchors_found": int(self.anchors_found),
            "anchors_expected": int(self.anchors_expected),
        }


class OCREngine:
    def __init__(self, strategies: list[type[AnchorBasedStrategy]]):
        self._strategies = strategies

    def preprocess_image(self, image: np.ndarray | bytes) -> np.ndarray:
        if isinstance(image, bytes):
            img = cv2.imdecode(np.frombuffer(image, np.uint8), cv2.IMREAD_COLOR)
        else:
            img = image

        if img is None:
            raise ValueError("Failed to decode image")

        img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        height, width = img.shape[:2]
        if height >= 1024 or width >= 1024:
            img = cv2.GaussianBlur(img, (3, 3), 0)

        clahe = cv2.createCLAHE(clipLimit=3.0, tileGridSize=(8, 8))
        img = clahe.apply(img)
        img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
        return img

    def find_anchors(self, ocr_result: OCRResult, translations: dict) -> Anchors:
        total_positions: list[BoundingRect] = []

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

        for text, box in zip(ocr_result.texts, ocr_result.boxes):
            text_lower = text.lower().strip()
            rect = BoundingRect.from_ndarray(box)
            if text_lower in translations["home"]:
                home = rect
            elif text_lower in translations["away"]:
                away = rect
            elif text_lower in translations["score"]:
                score = rect
            elif text_lower in translations["goal"]:
                goal = rect
            elif text_lower in translations["assist"]:
                assist = rect
            elif text_lower in translations["passes"]:
                passing = rect
            elif text_lower in translations["interception"]:
                interception = rect
            elif text_lower in translations["save"]:
                save = rect
            elif text_lower in translations["total"]:
                total_positions.append(rect)

        if home and away:
            for total_position in total_positions:
                if home.top_edge < total_position.top_edge < away.top_edge:
                    home_total = total_position
                elif total_position.top_edge > away.top_edge:
                    away_total = total_position

        return Anchors(
            home=home,
            away=away,
            score=score,
            goal=goal,
            assist=assist,
            passing=passing,
            interception=interception,
            save=save,
            home_total=home_total,
            away_total=away_total,
        )

    def scan(
        self,
        image: np.ndarray | bytes,
        *,
        min_quality_score: float = 0.5,
        log: Callable[..., None] | None = None,
    ) -> tuple[OCRParsedResult, Anchors, OCRResult, np.ndarray, dict[str, Any]]:
        log = log or (lambda *args: None)

        preprocessed = self.preprocess_image(image)

        paddle = _get_paddle_ocr()
        with _ocr_lock:
            raw = paddle.predict(preprocessed)

        if not raw or not isinstance(raw, list) or not raw[0]:
            raise RuntimeError("PaddleOCR returned empty result")

        result0 = raw[0]
        if not isinstance(result0, dict):
            raise RuntimeError("Unexpected PaddleOCR output format")

        texts = result0.get("rec_texts")
        boxes = result0.get("rec_boxes")
        if texts is None or boxes is None:
            raise RuntimeError("PaddleOCR output missing rec_texts/rec_boxes")
        if len(texts) != len(boxes):
            raise RuntimeError("PaddleOCR output rec_texts/rec_boxes length mismatch")

        ocr_result = OCRResult(list(texts), list(boxes))

        anchors = Anchors()
        for translations in ANCHOR_TRANSLATIONS:
            found_anchors = self.find_anchors(ocr_result, translations)
            if found_anchors.all_found_count() > anchors.all_found_count():
                anchors = found_anchors
                break

        best_result: OCRParsedResult | None = None
        best_score = 0.0
        best_strategy_name = ""

        for strategy_cls in self._strategies:
            log(f"Trying strategy: {strategy_cls.__name__}")
            built: AnchorBasedStrategy = strategy_cls(ocr_result, anchors, log)
            parsed = built.parse()
            quality_score = built.calculate_quality_score(parsed)
            log(f"Strategy {strategy_cls.__name__} quality score: {quality_score:.2f}")

            if quality_score > best_score:
                best_score = quality_score
                best_result = parsed
                best_strategy_name = strategy_cls.__name__

        meta = ScanMeta(
            best_strategy=best_strategy_name,
            best_score=best_score,
            min_quality_score=min_quality_score,
            anchors_found=anchors.all_found_count(),
            anchors_expected=len(anchors.all_anchors()),
        ).to_dict()

        if best_result and best_score >= min_quality_score:
            log(f"Best strategy score: {best_score:.2f}")
            return best_result, anchors, ocr_result, preprocessed, meta

        log(f"No strategy met minimum quality score of {min_quality_score}")
        return OCRParsedResult([], []), anchors, ocr_result, preprocessed, meta

    def build_debug_overlay(
        self, preprocessed_bgr: np.ndarray, anchors: Anchors, ocr_result: OCRResult
    ) -> np.ndarray:
        debug_img = preprocessed_bgr.copy()

        def draw(rect: BoundingRect | None, color: tuple[int, int, int]):
            if rect is None:
                return
            cv2.rectangle(debug_img, rect.top_left, rect.bottom_right, color, 2)

        draw(anchors.home_box, (0, 255, 0))
        draw(anchors.away_box, (255, 0, 0))
        draw(anchors.home_goal_box, (0, 0, 255))
        draw(anchors.home_assist_box, (255, 255, 0))
        draw(anchors.home_passing_box, (0, 255, 255))
        draw(anchors.home_interception_box, (255, 0, 255))
        draw(anchors.home_save_box, (255, 255, 255))
        draw(anchors.home_score_box, (0, 255, 0))

        draw(anchors.away_goal_box, (0, 0, 255))
        draw(anchors.away_assist_box, (255, 255, 0))
        draw(anchors.away_passing_box, (0, 255, 255))
        draw(anchors.away_interception_box, (255, 0, 255))
        draw(anchors.away_save_box, (255, 255, 255))
        draw(anchors.away_score_box, (0, 255, 0))

        for box in ocr_result.boxes:
            rect = BoundingRect.from_ndarray(box)
            cv2.rectangle(debug_img, rect.top_left, rect.bottom_right, (0, 0, 255), 1)

        for rect in anchors.all_anchors():
            if rect is not None:
                cv2.rectangle(
                    debug_img, rect.top_left, rect.bottom_right, (255, 255, 0), 2
                )

        return debug_img
