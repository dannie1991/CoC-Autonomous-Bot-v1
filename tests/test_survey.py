from types import SimpleNamespace
from unittest.mock import Mock

import pytest

from cocbot.device import DeviceError
from cocbot.survey import capture_stage
from cocbot.vision import Screen


def test_survey_records_observation_without_game_input(tmp_path):
    runtime = Mock()
    runtime.vision.rules = {"resolution": [1920, 1080]}
    runtime.device.serial = "127.0.0.1:5555"
    runtime.probe.return_value = SimpleNamespace(
        width=1920, height=1080, screen=Screen.UNKNOWN, reason="Uncalibrated menu"
    )
    path = capture_stage(runtime, "builders", tmp_path)
    assert path.name.startswith("progress-builders-")
    assert '"input_actions": 0' in path.with_suffix(".json").read_text()
    runtime.device.tap.assert_not_called()
    runtime.device.swipe.assert_not_called()


def test_survey_rejects_wrong_home_and_resolution(tmp_path):
    runtime = Mock()
    runtime.vision.rules = {"resolution": [1920, 1080]}
    runtime.probe.return_value = SimpleNamespace(
        width=1920, height=1080, screen=Screen.UNKNOWN, reason="Overlay"
    )
    with pytest.raises(DeviceError, match="clear HOME"):
        capture_stage(runtime, "home", tmp_path)
    runtime.probe.return_value.width = 1280
    with pytest.raises(DeviceError, match="resolution"):
        capture_stage(runtime, "builders", tmp_path)
    runtime.device.tap.assert_not_called()
