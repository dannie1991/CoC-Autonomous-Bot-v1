"""Bounded collection of calibrated resource bubbles in a verified home village."""

import time
from pathlib import Path

import cv2

from .device import DeviceError
from .telemetry import event
from .vision import Screen


class Collector:
    def __init__(self, runtime):
        self.runtime = runtime
        self.rules = runtime.vision.rules
        if (
            not self.rules
            or not self.rules.get("account")
            or not self.rules.get("resources")
        ):
            raise ValueError(
                "Collection needs a local profile with account and resource templates"
            )

    def _read_template(self, file):
        image = cv2.imread(str(self.runtime.vision.profile.parent / file))
        if image is None or image.std() < 2:
            raise ValueError(f"Invalid collection template: {file}")
        return image

    def _target(self, path):
        image = cv2.imread(str(path))
        account = self.rules["account"]
        x, y, w, h = account["region"]
        template = self._read_template(account["file"])
        crop = image[y : y + h, x : x + w]
        # Compare the text foreground, not the moving village behind it.
        if crop.shape != template.shape:
            raise DeviceError("Player name region has changed")
        expected = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY) > 210
        actual = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY) > 210
        if (expected != actual).mean() > 0.005:
            raise DeviceError("Player name does not match the calibrated account")
        x, y, w, h = self.rules["village_region"]
        village = image[y : y + h, x : x + w]
        targets = []
        for resource in self.rules["resources"]:
            template = self._read_template(resource["file"])
            if (
                village.shape[0] < template.shape[0]
                or village.shape[1] < template.shape[1]
            ):
                raise ValueError("Resource template exceeds village region")
            _, score, _, point = cv2.minMaxLoc(
                cv2.matchTemplate(village, template, cv2.TM_CCOEFF_NORMED)
            )
            px, py = point
            crop = village[py : py + template.shape[0], px : px + template.shape[1]]
            if score >= 0.94 and cv2.absdiff(crop, template).mean() <= 15:
                targets.append(
                    (
                        score,
                        resource["name"],
                        x + px + template.shape[1] // 2,
                        y + py + template.shape[0] // 2,
                    )
                )
        return max(targets) if targets else None

    def run(self, output: Path, execute: bool = False, limit: int = 8):
        if not 1 <= limit <= 20:
            raise ValueError("Collection limit must be between 1 and 20")
        output.mkdir(parents=True, exist_ok=True)
        actions = []
        for index in range(limit + 1):
            shot = output / f"collect-{time.time_ns()}.png"
            obs = self.runtime.probe(shot)
            if obs.screen is not Screen.HOME:
                raise DeviceError(
                    f"Collection stopped: screen={obs.screen.name} ({obs.reason})"
                )
            target = self._target(shot)
            if target is None:
                return {
                    "actions": actions,
                    "stop": "no_resource_bubbles",
                    "executed": execute,
                }
            score, name, x, y = target
            if any(
                abs(action["x"] - x) < 20 and abs(action["y"] - y) < 20
                for action in actions
            ):
                raise DeviceError(
                    "Resource bubble remains after input; stopped without retrying"
                )
            if index == limit:
                return {"actions": actions, "stop": "limit", "executed": execute}
            action = {"resource": name, "x": x, "y": y, "confidence": score}
            event("collect_plan", **action, execute=execute)
            if not execute:
                return {"actions": [action], "stop": "dry_run", "executed": False}
            # No automatic retry after input: its outcome may be uncertain.
            self.runtime.device.tap(x, y)
            actions.append(action)
            time.sleep(max(0.5, self.runtime.settings.poll_interval))
        raise AssertionError("Unreachable")
