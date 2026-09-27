import argparse
import json
import time
from dataclasses import asdict, replace

from .config import Settings
from .device import DeviceError
from .runtime import Runtime
from .telemetry import configure_logging


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="cocbot")
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--doctor", action="store_true", help="Verify MuMu and ADB; no input")
    mode.add_argument(
        "--observe",
        type=int,
        metavar="COUNT",
        help="Capture COUNT observations; no taps",
    )
    parser.add_argument("--adb", help="ADB executable path")
    parser.add_argument("--serial", help="Explicit device serial or host:port")
    args = parser.parse_args(argv)
    if args.observe is not None and args.observe < 1:
        parser.error("--observe must be positive")
    if not args.doctor and args.observe is None:
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
