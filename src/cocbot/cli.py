import argparse
import json
import time
from dataclasses import asdict, replace
from pathlib import Path

from .collector import Collector
from .config import Settings
from .device import DeviceError
from .runtime import Runtime
from .telemetry import configure_logging


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cocbot")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--probe",
        action="store_true",
        help="Connect and capture one screenshot; no taps",
    )
    mode.add_argument(
        "--observe",
        type=int,
        metavar="COUNT",
        help="Capture COUNT observations; no taps",
    )
    mode.add_argument(
        "--collect",
        action="store_true",
        help="Plan one resource collection (dry run by default)",
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute bounded --collect on the calibrated account",
    )
    parser.add_argument("--adb", help="ADB executable path")
    parser.add_argument("--serial", help="Explicit device serial or host:port")
    parser.add_argument("--profile", type=Path, help="Calibrated vision profile JSON")
    parser.add_argument("--output", type=Path, default=Path("artifacts"))
    args = parser.parse_args(argv)
    if args.observe is not None and args.observe < 1:
        parser.error("--observe must be positive")
    if args.execute and not args.collect:
        parser.error("--execute requires --collect")
    if not args.probe and args.observe is None and not args.collect:
        parser.print_help()
        return 0
    configure_logging()
    try:
        settings = Settings()
        if args.adb:
            settings = replace(settings, adb_path=args.adb)
        if args.serial:
            settings = replace(settings, adb_serial=args.serial)
        runtime = Runtime(settings, args.profile)
        args.output.mkdir(parents=True, exist_ok=True)
        if args.collect:
            result = Collector(runtime).run(args.output, execute=args.execute)
            report_path = args.output / f"collection-{time.time_ns()}.json"
            report_path.write_text(json.dumps(result, indent=2), encoding="utf-8")
            print(json.dumps(result))
            return 0
        for index in range(args.observe or 1):
            path = args.output / (
                f"observation-{time.time_ns()}.png" if args.observe else "probe.png"
            )
            obs = runtime.probe(path)
            report = {
                **asdict(obs),
                "screen": obs.screen.name,
                "serial": runtime.device.serial,
                "screenshot": str(path),
                "timestamp": time.time(),
                "input_actions": 0,
            }
            path.with_suffix(".json").write_text(
                json.dumps(report, indent=2), encoding="utf-8"
            )
            print(
                f"ADB OK - screenshot {obs.width}x{obs.height}, screen={obs.screen.name}, confidence={obs.confidence:.3f}"
            )
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
