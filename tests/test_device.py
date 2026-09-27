import io
from unittest.mock import Mock

from PIL import Image

from cocbot.device import AdbDevice


def test_screenshot_stays_in_memory():
    buffer = io.BytesIO()
    Image.new("RGB", (20, 10)).save(buffer, format="PNG")
    device = AdbDevice()
    device._cmd = Mock(return_value=Mock(stdout=buffer.getvalue()))
    assert device.screenshot_png() == buffer.getvalue()
