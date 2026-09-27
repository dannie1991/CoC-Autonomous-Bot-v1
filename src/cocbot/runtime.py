from __future__ import annotations

import time

from .config import Settings
from .device import AdbDevice, DeviceError
from .progression import (
    Currency,
    UpgradeProposal,
    decide_upgrade,
    parse_amount,
    parse_town_hall,
    read_village_progress,
)
from .telemetry import event
from .vision import Observation, Screen, Vision


class Runtime:
    MIN_ACTION_CONFIDENCE = 0.85

    def __init__(self, settings: Settings):
        self.settings = settings
        self.device = AdbDevice(
            settings.adb_path, settings.adb_serial, settings.screenshot_timeout
        )
        self.vision = Vision()

    def probe(self):
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation = self.vision.observe_png(self.device.screenshot_png())
        event("probe", observation=observation, frame_saved=False)
        return observation

    def status(self):
        """Inspect one frame in memory; this method never sends device input."""
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation, texts = self.vision.inspect_png(self.device.screenshot_png())
        progress = read_village_progress(texts, observation.width, observation.height)
        event("status", observation=observation, progress=progress, frame_saved=False)
        return observation, progress

    def _wait_for_screen(self, expected: set[Screen]) -> Observation:
        """Poll a bounded time for a post-action screen transition."""
        deadline = time.monotonic() + max(2.0, self.settings.screenshot_timeout)
        last = None
        while time.monotonic() < deadline:
            observation, _ = self.vision.inspect_png(self.device.screenshot_png())
            last = observation
            if observation.screen in expected:
                return observation
            time.sleep(self.settings.poll_interval)
        if last is None:
            raise DeviceError("No post-action screen was observed")
        expected_names = ", ".join(screen.name for screen in expected)
        raise DeviceError(
            f"Expected {expected_names}, got {last.screen.name} ({last.reason})"
        )

    def open_attack_menu(self, execute: bool = False) -> dict:
        """Open the live OCR-confirmed Attack button, only when explicitly executed."""
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation, texts = self.vision.inspect_png(self.device.screenshot_png())
        if observation.screen is not Screen.HOME:
            raise DeviceError("Attack menu requires a recognised HOME screen")
        matches = [
            text
            for text in texts
            if self.vision._normalise(text.value) == "attack"
            and text.confidence >= 0.85
            and text.center is not None
        ]
        if len(matches) != 1:
            raise DeviceError("Expected one high-confidence Attack button")
        target = matches[0]
        x = round(target.center[0])
        # Clash renders the button label near its lower edge; use the centre of
        # the visible button body rather than tapping the label itself.
        y = round(target.center[1] - observation.height * 0.068)
        plan = {"label": "Attack", "x": x, "y": y, "confidence": target.confidence}
        event("open_attack_menu_plan", **plan, execute=execute)
        if not execute:
            return {"executed": False, "plan": plan}
        self.device.tap(x, y)
        time.sleep(max(0.5, self.settings.poll_interval))
        after, _ = self.vision.inspect_png(self.device.screenshot_png())
        if after.screen is not Screen.ATTACK_MENU:
            raise DeviceError(
                f"Attack tap was not confirmed: screen={after.screen.name} ({after.reason})"
            )
        event("open_attack_menu_confirmed", screen=after.screen.name)
        return {"executed": True, "plan": plan, "screen": after.screen.name}

    def reload_after_inactivity(self, execute: bool = False) -> dict:
        """Reload only the recognised Clash inactivity popup and verify HOME."""
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation, texts = self.vision.inspect_png(self.device.screenshot_png())
        if observation.screen is not Screen.POPUP:
            raise DeviceError("Reload requires a recognised inactivity popup")
        matches = [
            text
            for text in texts
            if self.vision._normalise(text.value).replace(" ", "") == "reloadgame"
            and text.confidence >= 0.85
            and text.center is not None
        ]
        if len(matches) != 1:
            raise DeviceError("Expected one high-confidence Reload Game button")
        target = matches[0]
        x, y = (round(value) for value in target.center)
        plan = {"label": "Reload Game", "x": x, "y": y, "confidence": target.confidence}
        event("reload_game_plan", **plan, execute=execute)
        if not execute:
            return {"executed": False, "plan": plan}
        self.device.tap(x, y)
        after = self._wait_for_screen({Screen.HOME})
        event("reload_game_confirmed", screen=after.screen.name)
        return {"executed": True, "plan": plan, "screen": after.screen.name}

    def find_match(self, execute: bool = False) -> dict:
        """Open matchmaking only from the live OCR-confirmed attack menu."""
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation, texts = self.vision.inspect_png(self.device.screenshot_png())
        if observation.screen is not Screen.ATTACK_MENU:
            raise DeviceError("Find a Match requires a recognised attack menu")
        matches = [
            text
            for text in texts
            if self.vision._normalise(text.value) == "find a match"
            and text.confidence >= 0.85
            and text.center is not None
        ]
        if len(matches) != 1:
            raise DeviceError("Expected one high-confidence Find a Match button")
        target = matches[0]
        x, y = (round(value) for value in target.center)
        plan = {"label": "Find a Match", "x": x, "y": y, "confidence": target.confidence}
        event("find_match_plan", **plan, execute=execute)
        if not execute:
            return {"executed": False, "plan": plan}
        self.device.tap(x, y)
        time.sleep(max(1.0, self.settings.poll_interval))
        after, _ = self.vision.inspect_png(self.device.screenshot_png())
        if after.screen is not Screen.ARMY:
            raise DeviceError(
                f"Find a Match tap was not confirmed: screen={after.screen.name} ({after.reason})"
            )
        event("find_match_confirmed", screen=after.screen.name)
        return {"executed": True, "plan": plan, "screen": after.screen.name}

    def start_matchmaking(self, execute: bool = False) -> dict:
        """Start matchmaking only from the live OCR-confirmed My Army screen."""
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation, texts = self.vision.inspect_png(self.device.screenshot_png())
        if observation.screen is not Screen.ARMY:
            raise DeviceError("Matchmaking requires a recognised My Army screen")
        matches = [
            text
            for text in texts
            if self.vision._normalise(text.value) == "attack"
            and text.confidence >= 0.85
            and text.center is not None
        ]
        if len(matches) != 1:
            raise DeviceError("Expected one high-confidence My Army Attack button")
        target = matches[0]
        x, y = (round(value) for value in target.center)
        plan = {"label": "Attack", "x": x, "y": y, "confidence": target.confidence}
        event("start_matchmaking_plan", **plan, execute=execute)
        if not execute:
            return {"executed": False, "plan": plan}
        self.device.tap(x, y)
        time.sleep(max(1.0, self.settings.poll_interval))
        after, _ = self.vision.inspect_png(self.device.screenshot_png())
        if after.screen not in {Screen.SEARCHING, Screen.BATTLE}:
            raise DeviceError(
                f"Matchmaking tap was not confirmed: screen={after.screen.name} ({after.reason})"
            )
        event("start_matchmaking_confirmed", screen=after.screen.name)
        return {"executed": True, "plan": plan, "screen": after.screen.name}

    def return_home(self, execute: bool = False) -> dict:
        """Close only the live OCR-confirmed results screen and verify HOME."""
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation, texts = self.vision.inspect_png(self.device.screenshot_png())
        if observation.screen is not Screen.RESULTS:
            raise DeviceError("Return Home requires a recognised results screen")
        matches = [
            text
            for text in texts
            if self.vision._normalise(text.value) == "return home"
            and text.confidence >= 0.85
            and text.center is not None
        ]
        if len(matches) != 1:
            raise DeviceError("Expected one high-confidence Return Home button")
        target = matches[0]
        x, y = (round(value) for value in target.center)
        plan = {"label": "Return Home", "x": x, "y": y, "confidence": target.confidence}
        event("return_home_plan", **plan, execute=execute)
        if not execute:
            return {"executed": False, "plan": plan}
        self.device.tap(x, y)
        time.sleep(max(1.0, self.settings.poll_interval))
        after, _ = self.vision.inspect_png(self.device.screenshot_png())
        if after.screen is Screen.POPUP:
            event("return_home_needs_recovery", screen=after.screen.name)
            return {
                "executed": True,
                "plan": plan,
                "screen": after.screen.name,
                "recovery_required": True,
            }
        if after.screen is not Screen.HOME:
            raise DeviceError(
                f"Return Home was not confirmed: screen={after.screen.name} ({after.reason})"
            )
        event("return_home_confirmed", screen=after.screen.name)
        return {"executed": True, "plan": plan, "screen": after.screen.name}

    def collect_once(self, execute: bool = False) -> dict:
        """Collect one live OCR-confirmed village reward and verify the frame."""
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation, texts = self.vision.inspect_png(self.device.screenshot_png())
        if observation.screen is not Screen.HOME:
            raise DeviceError("Collect requires a recognised HOME screen")
        matches = [
            text
            for text in texts
            if self.vision._normalise(text.value) == "collect"
            and text.confidence >= 0.85
            and text.center is not None
        ]
        if len(matches) != 1:
            raise DeviceError("Expected one high-confidence Collect indicator")
        before = read_village_progress(texts, observation.width, observation.height).resources
        target = matches[0]
        x = round(target.center[0])
        if target.center[1] >= observation.height * 0.75:
            # Loot Cart renders Collect at the bottom of its large button.
            y = round(target.center[1] - observation.height * 0.045)
        else:
            # A collector speech label floats above the collectible building.
            y = round(target.center[1] + observation.height * 0.04)
        plan = {"label": "Collect", "x": x, "y": y, "confidence": target.confidence}
        event("collect_plan", **plan, execute=execute)
        if not execute:
            return {"executed": False, "plan": plan}
        self.device.tap(x, y)
        time.sleep(max(0.5, self.settings.poll_interval))
        after, after_texts = self.vision.inspect_png(self.device.screenshot_png())
        if after.screen is not Screen.HOME:
            raise DeviceError(
                f"Collect tap was not confirmed: screen={after.screen.name} ({after.reason})"
            )
        after_resources = read_village_progress(
            after_texts, after.width, after.height
        ).resources
        still_collecting = any(
            self.vision._normalise(text.value) == "collect" for text in after_texts
        )
        changed = before != after_resources or not still_collecting
        if not changed:
            raise DeviceError("Collect tap did not change the live village observation")
        event("collect_confirmed", resources=after_resources, indicator_cleared=not still_collecting)
        return {
            "executed": True,
            "plan": plan,
            "resources": after_resources,
            "indicator_cleared": not still_collecting,
        }

    def laboratory_upgrade_plan(self) -> dict:
        """Read one selected Laboratory upgrade without performing any input."""
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation, texts = self.vision.inspect_png(self.device.screenshot_png())
        if observation.screen is not Screen.LABORATORY:
            raise DeviceError("Laboratory upgrade plan requires a recognised Laboratory screen")
        upgrades = [
            text
            for text in texts
            if self.vision._normalise(text.value) == "upgrade"
            and text.confidence >= 0.85
            and text.center is not None
        ]
        if len(upgrades) != 1:
            raise DeviceError("Expected one high-confidence Upgrade button")
        upgrade = upgrades[0]
        candidates = []
        for text in texts:
            if text.center is None or text.confidence < 0.75:
                continue
            amount = parse_amount(text.value)
            if amount is None:
                continue
            x, y = text.center
            button_x, button_y = upgrade.center
            if abs(x - button_x) <= observation.width * 0.1 and button_y - 180 <= y < button_y:
                candidates.append((text.confidence, amount))
        if len(candidates) != 1:
            raise DeviceError("Expected one readable cost above the Upgrade button")
        _, cost = candidates[0]
        progress = read_village_progress(texts, observation.width, observation.height)
        proposal = UpgradeProposal("Laboratory", Currency.ELIXIR, cost)
        available = progress.resources.elixir if progress.resources else None
        decision = decide_upgrade(proposal, available, progress.builders, progress.confidence)
        return {
            "proposal": proposal,
            "available": available,
            "builders": progress.builders,
            "allowed": decision.allowed,
            "reason": decision.reason,
        }

    def town_hall_status(self) -> dict:
        """Read the selected Town Hall state without sending any input."""
        self.device.connect()
        if not self.device.ping():
            raise RuntimeError("ADB device is not ready")
        observation, texts = self.vision.inspect_png(self.device.screenshot_png())
        if observation.screen is not Screen.TOWN_HALL:
            raise DeviceError("Town Hall status requires a selected recognised Town Hall")
        levels = {
            level
            for text in texts
            if text.confidence >= Runtime.MIN_ACTION_CONFIDENCE
            for level in [parse_town_hall(text.value)]
            if level is not None
        }
        normalised = {self.vision._normalise(text.value) for text in texts}
        return {
            "town_hall": levels.pop() if len(levels) == 1 else None,
            "under_construction": "cancel" in normalised,
            "upgrade_available": "upgrade" in normalised,
            "input_actions": 0,
        }

    @staticmethod
    def action_gate(observation, progress) -> tuple[bool, str]:
        """Return whether a future action layer may consider a new proposal.

        This is deliberately a gate only: it cannot send device input.
        """
        if observation.screen is not Screen.HOME:
            return False, "Live screen is not a uniquely recognised HOME screen"
        if observation.confidence < Runtime.MIN_ACTION_CONFIDENCE:
            return False, "HOME recognition confidence is below 0.85"
        if progress.confidence < 0.95:
            return False, "Builders or Town Hall are not fully verified"
        if (
            progress.resources is None
            or progress.resources.confidence < Runtime.MIN_ACTION_CONFIDENCE
            or progress.resources.gold is None
            or progress.resources.elixir is None
        ):
            return False, "Gold and elixir values are not fully verified"
        return True, "Live HOME observation is complete"
