"""OCR adapter for transient emulator frames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class DetectedText:
    value: str
    confidence: float
    box: tuple[int, int, int, int] | None = None

    @property
    def center(self) -> tuple[float, float] | None:
        if self.box is None:
            return None
        left, top, right, bottom = self.box
        return (left + right) / 2, (top + bottom) / 2


class TextReader(Protocol):
    def read(self, image: np.ndarray) -> list[DetectedText]: ...


class RapidTextReader:
    """Lazy RapidOCR wrapper so importing the CLI never downloads models."""

    def __init__(self):
        try:
            from rapidocr_onnxruntime import RapidOCR
        except ImportError as exc:
            raise RuntimeError("RapidOCR is unavailable in this installation") from exc
        self._reader = RapidOCR()

    def read(self, image: np.ndarray) -> list[DetectedText]:
        result, _ = self._reader(image)
        texts = []
        for box, value, confidence in result or []:
            xs, ys = zip(*box, strict=True)
            texts.append(
                DetectedText(
                    value=value,
                    confidence=float(confidence),
                    box=(int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))),
                )
            )
        return texts
