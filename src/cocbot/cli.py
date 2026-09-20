import argparse
from .config import Settings
from .runtime import Runtime
from .telemetry import configure_logging

def main() -> int:
    parser = argparse.ArgumentParser(prog="cocbot")
    parser.add_argument("--probe", action="store_true", help="Verify ADB and capture one screenshot")
    args = parser.parse_args()
    configure_logging()
    runtime = Runtime(Settings())
    if args.probe:
        obs = runtime.probe()
        print(f"ADB OK - screenshot {obs.width}x{obs.height}, screen={obs.screen.name}")
        return 0
    parser.print_help()
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
