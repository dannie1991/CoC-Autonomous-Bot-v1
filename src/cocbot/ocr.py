"""OCR adapter for transient emulator frames."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np


@dataclass(frozen=True)
class DetectedText:
    value: str
    confidence: float


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
        return [DetectedText(value=item[1], confidence=float(item[2])) for item in result or []]
