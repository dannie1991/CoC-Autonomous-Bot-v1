import io
import json
import subprocess
from unittest.mock import Mock

import cv2
import numpy as np
import pytest
from PIL import Image

from cocbot.collector import Collector
from cocbot.config import Settings
from cocbot.device import AdbDevice, DeviceError
from cocbot.vision import Screen, Vision


def test_settings_read_environment_at_construction(monkeypatch):
    monkeypatch.setenv("COCBOT_ADB_SERIAL", "new-address:5555")
    assert Settings().adb_serial == "new-address:5555"


@pytest.mark.parametrize("value", [0, -1, float("nan"), float("inf")])
def test_settings_reject_invalid_timeout(value):
    with pytest.raises(ValueError):
        Settings(screenshot_timeout=value)


def test_mumu_uses_reported_host(tmp_path, monkeypatch):
    (tmp_path / "MuMuManager.exe").touch()
    info = {
        "index": "0",
        "is_process_started": True,
        "adb_host_ip": "192.168.1.86",
        "adb_port": 5555,
    }
    monkeypatch.setattr(
        subprocess, "run", Mock(return_value=Mock(stdout=json.dumps(info)))
    )
    device = AdbDevice(str(tmp_path / "adb.exe"))
    device._cmd = Mock(side_effect=[Mock(stdout="connected"), Mock(stdout="device")])
    assert device.connect() == "192.168.1.86:5555"


@pytest.mark.parametrize(
    "listing", ["", "a\tunauthorized\n", "a\tdevice\nb\tdevice\n", "a\toffline\n"]
)
def test_refuse_missing_ambiguous_or_unready_devices(listing):
    device = AdbDevice()
    device._cmd = Mock(return_value=Mock(stdout="List of devices attached\n" + listing))
    with pytest.raises(DeviceError):
        device.connect()


def test_corrupt_screenshot_preserves_previous_file(tmp_path):
    path = tmp_path / "capture.png"
    path.write_bytes(b"previous")
    device = AdbDevice()
    device._cmd = Mock(return_value=Mock(stdout=b"error: offline"))
    with pytest.raises(DeviceError):
        device.screenshot(path)
    assert path.read_bytes() == b"previous"


def test_binary_screenshot(tmp_path):
    buffer = io.BytesIO()
    Image.new("RGB", (20, 10)).save(buffer, format="PNG")
    device = AdbDevice()
    device._cmd = Mock(return_value=Mock(stdout=buffer.getvalue()))
    path = device.screenshot(tmp_path / "capture.png")
    assert Image.open(path).size == (20, 10)


@pytest.fixture
def calibrated(tmp_path):
    image = np.random.default_rng(2).integers(0, 255, (100, 200, 3), dtype=np.uint8)
    anchors = []
    for index, x in enumerate((0, 50)):
        cv2.imwrite(str(tmp_path / f"{index}.png"), image[0:20, x : x + 20])
        anchors.append({"file": f"{index}.png", "region": [x, 0, 20, 20]})
    rules = {"resolution": [200, 100], "screens": {"HOME": anchors}}
    profile = tmp_path / "profile.json"
    profile.write_text(json.dumps(rules))
    return image, profile, tmp_path / "screen.png"


def test_home_requires_all_anchors_and_brightness(calibrated):
    image, profile, path = calibrated
    vision = Vision(profile)
    cv2.imwrite(str(path), image)
    assert vision.observe(path).screen is Screen.HOME
    cv2.imwrite(str(path), (image * 0.5).astype(np.uint8))
    assert vision.observe(path).screen is Screen.UNKNOWN
    image[0:20, 0:20] = 0
    cv2.imwrite(str(path), image)
    assert vision.observe(path).screen is Screen.UNKNOWN


def test_resolution_mismatch(calibrated):
    image, profile, path = calibrated
    cv2.imwrite(str(path), image[:50])
    assert Vision(profile).observe(path).screen is Screen.UNKNOWN


def test_collection_refuses_unknown_screen(calibrated, tmp_path):
    _, profile, path = calibrated
    vision = Vision(profile)
    vision.rules.update(account={"file": "0.png"}, resources=[{"name": "gold"}])
    runtime = Mock(vision=vision)
    runtime.probe.return_value.screen = Screen.UNKNOWN
    runtime.probe.return_value.reason = "modal"
    with pytest.raises(DeviceError, match="Collection stopped"):
        Collector(runtime).run(tmp_path, execute=True)
    runtime.device.tap.assert_not_called()
