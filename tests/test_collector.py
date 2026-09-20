from types import SimpleNamespace
from unittest.mock import Mock

import cv2
import numpy as np
import pytest

from cocbot.collector import Collector
from cocbot.device import DeviceError
from cocbot.vision import Screen


@pytest.fixture
def collector(tmp_path):
    runtime = Mock()
    runtime.vision.rules = {
        "account": {"file": "name.png", "region": [0, 0, 40, 20]},
        "resources": [{"file": "coin.png", "name": "gold"}],
        "village_region": [0, 20, 100, 80],
    }
    runtime.vision.profile = tmp_path / "profile.json"
    runtime.settings.poll_interval = 0.01
    runtime.probe.return_value = SimpleNamespace(screen=Screen.HOME)
    return Collector(runtime)


def test_dry_run_never_taps(collector, tmp_path):
    collector._target = Mock(return_value=(1.0, "gold", 50, 50))
    report = collector.run(tmp_path)
    assert report["stop"] == "dry_run"
    collector.runtime.device.tap.assert_not_called()


def test_observe_after_every_action(collector, tmp_path, monkeypatch):
    monkeypatch.setattr("cocbot.collector.time.sleep", lambda _: None)
    collector._target = Mock(side_effect=[(1.0, "gold", 50, 50), None])
    report = collector.run(tmp_path, execute=True)
    assert report["stop"] == "no_resource_bubbles"
    assert collector.runtime.probe.call_count == 2
    collector.runtime.device.tap.assert_called_once_with(50, 50)


def test_no_retry_after_uncertain_input(collector, tmp_path):
    collector._target = Mock(return_value=(1.0, "gold", 50, 50))
    collector.runtime.device.tap.side_effect = DeviceError("timeout")
    with pytest.raises(DeviceError):
        collector.run(tmp_path, execute=True)
    assert collector.runtime.device.tap.call_count == 1


def test_unchanged_bubble_stops(collector, tmp_path, monkeypatch):
    monkeypatch.setattr("cocbot.collector.time.sleep", lambda _: None)
    collector._target = Mock(return_value=(1.0, "gold", 50, 50))
    with pytest.raises(DeviceError, match="without retrying"):
        collector.run(tmp_path, execute=True)
    assert collector.runtime.device.tap.call_count == 1


def test_account_change_blocks_taps(collector, tmp_path):
    image = np.zeros((100, 100, 3), dtype=np.uint8)
    cv2.putText(image, "A", (0, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    cv2.imwrite(str(tmp_path / "name.png"), image[:20, :40])
    image[:20] = 0
    cv2.putText(image, "B", (0, 17), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    path = tmp_path / "other.png"
    cv2.imwrite(str(path), image)
    with pytest.raises(DeviceError, match="Player name"):
        collector._target(path)
    collector.runtime.device.tap.assert_not_called()
