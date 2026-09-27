import io

import pytest
from PIL import Image

from cocbot.ocr import DetectedText
from cocbot.vision import Screen, Vision


def png(width, height):
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color="black").save(buffer, format="PNG")
    return buffer.getvalue()


def vision_with(*texts):
    return Vision(lambda _: [DetectedText(value, score) for value, score in texts])


def test_home_is_recognised_from_live_english_ui_text():
    observation = vision_with(("Attack", 0.99), ("Shop", 0.95)).observe_png(png(1920, 1080))
    assert observation.screen is Screen.HOME
    assert observation.confidence == 0.95


def test_ambiguous_or_low_confidence_text_stops_recognition():
    ambiguous = vision_with(("Attack", 0.99), ("Shop", 0.99), ("Return Home", 0.99))
    assert ambiguous.observe_png(png(1920, 1080)).screen is Screen.UNKNOWN
    low_confidence = vision_with(("Attack", 0.74), ("Shop", 0.99))
    assert low_confidence.observe_png(png(1920, 1080)).screen is Screen.UNKNOWN
    incomplete = vision_with(("Attack", 0.99))
    assert incomplete.observe_png(png(1920, 1080)).screen is Screen.UNKNOWN


def test_unsupported_resolution_is_rejected():
    observation = Vision().observe_png(png(1000, 1000))
    assert observation.screen is Screen.UNKNOWN
    assert observation.reason == "Unsupported emulator resolution"


def test_invalid_png_is_rejected():
    with pytest.raises(ValueError, match="decode"):
        Vision().observe_png(b"not a png")
