"""Capture evidence for progression calibration without sending game input."""

import json
import time
from pathlib import Path

from .device import DeviceError
from .vision import Screen

STAGES = ("home", "builders", "building", "upgrade", "confirmation")


def capture_stage(runtime, stage: str, output: Path) -> Path:
    """Save one screenshot and its observation; never tap or swipe."""
    if stage not in STAGES:
        raise ValueError(f"Unknown survey stage: {stage}")
    output.mkdir(parents=True, exist_ok=True)
    image = output / f"progress-{stage}-{time.time_ns()}.png"
    observation = runtime.probe(image)
    profile = runtime.vision.rules
    if profile and [observation.width, observation.height] != profile["resolution"]:
        raise DeviceError("Survey screenshot resolution differs from the profile")
    if stage == "home" and profile and observation.screen is not Screen.HOME:
        raise DeviceError(f"Expected a clear HOME screen; got {observation.screen.name}")
    report = {
        "stage": stage,
        "screenshot": str(image),
        "serial": runtime.device.serial,
        "width": observation.width,
        "height": observation.height,
        "screen": observation.screen.name,
        "reason": observation.reason,
        "input_actions": 0,
    }
    image.with_suffix(".json").write_text(json.dumps(report, indent=2), encoding="utf-8")
    return image
