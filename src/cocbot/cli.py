import argparse
import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from .config import Settings
from .controller import Controller
from .device import DeviceError
from .priorities import load_priorities, priority_rank
from .progression import Currency, UpgradeProposal, decide_upgrade
from .runtime import Runtime
from .state import BotState
from .telemetry import configure_logging


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cocbot")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--doctor", action="store_true", help="Verify MuMu and ADB; no input")
    mode.add_argument(
        "--status",
        action="store_true",
        help="Inspect HOME and village status from one in-memory frame; no input",
    )
    mode.add_argument(
        "--observe",
        type=int,
        metavar="COUNT",
        help="Capture COUNT observations; no taps",
    )
    mode.add_argument(
        "--plan-upgrade",
        metavar="BUILDING",
        help="Dry-run one upgrade proposal from live status; no input",
    )
    mode.add_argument(
        "--watch",
        type=int,
        metavar="COUNT",
        help="Run COUNT read-only status checks and stop on recovery; no input",
    )
    mode.add_argument(
        "--open-attack-menu",
        action="store_true",
        help="Plan or explicitly execute the live OCR-confirmed Attack button",
    )
    mode.add_argument(
        "--recover",
        action="store_true",
        help="Plan or explicitly reload only the recognised inactivity popup",
    )
    mode.add_argument(
        "--find-match",
        action="store_true",
        help="Plan or explicitly execute the live OCR-confirmed Find a Match button",
    )
    mode.add_argument(
        "--start-matchmaking",
        action="store_true",
        help="Plan or explicitly execute the live OCR-confirmed My Army Attack button",
    )
    mode.add_argument(
        "--return-home",
        action="store_true",
        help="Plan or explicitly execute the live OCR-confirmed results Return Home button",
    )
    mode.add_argument(
        "--collect-once",
        action="store_true",
        help="Plan or explicitly execute one live OCR-confirmed Collect indicator",
    )
    mode.add_argument(
        "--plan-laboratory-upgrade",
        action="store_true",
        help="Read the selected Laboratory upgrade and make no input",
    )
    mode.add_argument(
        "--town-hall-status",
        action="store_true",
        help="Read the selected Town Hall state and make no input",
    )
    parser.add_argument("--adb", help="ADB executable path")
    parser.add_argument("--serial", help="Explicit device serial or host:port")
    parser.add_argument("--currency", choices=[currency.value for currency in Currency])
    parser.add_argument("--cost", type=int)
    parser.add_argument("--priority-file", type=Path)
    parser.add_argument(
        "--execute", action="store_true", help="Allow the selected input command to tap"
    )
    args = parser.parse_args(argv)
    if args.observe is not None and args.observe < 1:
        parser.error("--observe must be positive")
    if args.watch is not None and args.watch < 1:
        parser.error("--watch must be positive")
    if args.plan_upgrade and (args.currency is None or args.cost is None):
        parser.error("--plan-upgrade requires --currency and --cost")
    if (
        args.execute
        and not args.open_attack_menu
        and not args.recover
        and not args.find_match
        and not args.start_matchmaking
        and not args.return_home
        and not args.collect_once
    ):
        parser.error("--execute requires an input command")
    if (
        not args.doctor
        and not args.status
        and args.observe is None
        and not args.plan_upgrade
        and args.watch is None
        and not args.open_attack_menu
        and not args.recover
        and not args.find_match
        and not args.start_matchmaking
        and not args.return_home
        and not args.collect_once
        and not args.plan_laboratory_upgrade
        and not args.town_hall_status
    ):
        parser.print_help()
        return 0
    configure_logging()
    try:
        settings = Settings()
        if args.adb:
            settings = replace(settings, adb_path=args.adb)
        if args.serial:
            settings = replace(settings, adb_serial=args.serial)
        runtime = Runtime(settings)
        if args.doctor:
            obs = runtime.probe()
            print(json.dumps({"adb": "ready", "serial": runtime.device.serial, "resolution": [obs.width, obs.height], "supported": obs.reason != "Unsupported emulator resolution"}))
            return 0
        if args.status:
            obs, progress = runtime.status()
            action_ready, action_reason = runtime.action_gate(obs, progress)
            next_state = Controller().observe(obs.screen)
            print(
                json.dumps(
                    {
                        "screen": obs.screen.name,
                        "resolution": [obs.width, obs.height],
                        "screen_confidence": obs.confidence,
                        "reason": obs.reason,
                        "serial": runtime.device.serial,
                        "village": asdict(progress),
                        "action_ready": action_ready,
                        "action_reason": action_reason,
                        "next_state": next_state.name,
                        "input_actions": 0,
                        "frame_saved": False,
                    }
                )
            )
            return 0
        if args.watch is not None:
            controller = Controller()
            for index in range(args.watch):
                obs, progress = runtime.status()
                action_ready, action_reason = runtime.action_gate(obs, progress)
                next_state = controller.observe(obs.screen)
                print(
                    json.dumps(
                        {
                            "iteration": index + 1,
                            "screen": obs.screen.name,
                            "screen_confidence": obs.confidence,
                            "next_state": next_state.name,
                            "action_ready": action_ready,
                            "action_reason": action_reason,
                            "input_actions": 0,
                            "frame_saved": False,
                        }
                    )
                )
                if next_state is BotState.RECOVER:
                    return 2
                if index + 1 < args.watch:
                    time.sleep(settings.poll_interval)
            return 0
        if args.plan_upgrade:
            obs, progress = runtime.status()
            action_ready, action_reason = runtime.action_gate(obs, progress)
            priority = priority_rank(args.plan_upgrade, load_priorities(args.priority_file))
            currency = Currency(args.currency)
            available = (
                getattr(progress.resources, currency.value)
                if progress.resources is not None and currency is not Currency.GEMS
                else None
            )
            proposal = UpgradeProposal(args.plan_upgrade, currency, args.cost)
            decision = decide_upgrade(
                proposal, available, progress.builders, progress.confidence
            )
            allowed = action_ready and decision.allowed
            print(
                json.dumps(
                    {
                        "proposal": asdict(proposal),
                        "priority": priority,
                        "available": available,
                        "allowed": allowed,
                        "reason": decision.reason if action_ready else action_reason,
                        "input_actions": 0,
                        "frame_saved": False,
                    },
                    default=str,
                )
            )
            return 0
        if args.open_attack_menu:
            print(json.dumps(runtime.open_attack_menu(execute=args.execute)))
            return 0
        if args.recover:
            print(json.dumps(runtime.reload_after_inactivity(execute=args.execute)))
            return 0
        if args.find_match:
            print(json.dumps(runtime.find_match(execute=args.execute)))
            return 0
        if args.start_matchmaking:
            print(json.dumps(runtime.start_matchmaking(execute=args.execute)))
            return 0
        if args.return_home:
            print(json.dumps(runtime.return_home(execute=args.execute)))
            return 0
        if args.collect_once:
            print(json.dumps(runtime.collect_once(execute=args.execute), default=str))
            return 0
        if args.plan_laboratory_upgrade:
            print(json.dumps(runtime.laboratory_upgrade_plan(), default=str))
            return 0
        if args.town_hall_status:
            print(json.dumps(runtime.town_hall_status(), default=str))
            return 0
        for index in range(args.observe or 1):
            obs = runtime.probe()
            report = {
                **asdict(obs),
                "screen": obs.screen.name,
                "serial": runtime.device.serial,
                "timestamp": time.time(),
                "input_actions": 0,
                "frame_saved": False,
            }
            print(json.dumps(report))
            if index + 1 < (args.observe or 1):
                time.sleep(settings.poll_interval)
        return 0
    except (DeviceError, OSError, ValueError, KeyError, RuntimeError) as exc:
        print(f"Cannot observe: {exc}")
        return 1
    except KeyboardInterrupt:
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
