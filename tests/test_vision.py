from pathlib import Path
import cv2
import numpy as np
from cocbot.vision import Screen, Vision

def test_unknown_observation_reports_dimensions(tmp_path: Path):
    path = tmp_path / "screen.png"
    cv2.imwrite(str(path), np.zeros((720, 1280, 3), dtype=np.uint8))
    obs = Vision().observe(path)
    assert obs.screen is Screen.UNKNOWN
    assert (obs.width, obs.height) == (1280, 720)
