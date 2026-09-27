import io

import pytest
from PIL import Image

from cocbot.vision import Screen, Vision


def png(width, height):
    buffer = io.BytesIO()
    Image.new("RGB", (width, height), color="black").save(buffer, format="PNG")
    return buffer.getvalue()


def test_supported_live_frame_is_never_saved_or_profile_based():
    observation = Vision().observe_png(png(1920, 1080))
    assert observation.screen is Screen.UNKNOWN
    assert observation.confidence == 1.0
    assert "Live frame" in observation.reason


def test_unsupported_resolution_is_rejected():
    observation = Vision().observe_png(png(1000, 1000))
    assert observation.screen is Screen.UNKNOWN
    assert observation.reason == "Unsupported emulator resolution"


def test_invalid_png_is_rejected():
    with pytest.raises(ValueError, match="decode"):
        Vision().observe_png(b"not a png")
