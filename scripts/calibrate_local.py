"""Build the locally verified 1920x1080 BETAAA profile from a clear home screenshot.

These regions were inspected on this MuMu instance on 2026-09-20.
Do not reuse this calibration on an unrelated screenshot or another resolution.
"""

import argparse
import json
from pathlib import Path

import cv2


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("screenshot", type=Path)
    parser.add_argument("--output", type=Path, default=Path("profiles/local"))
    args = parser.parse_args()
    image = cv2.imread(str(args.screenshot))
    if image is None or image.shape[:2] != (1080, 1920):
        raise ValueError("Expected the verified 1920x1080 home screenshot")
    args.output.mkdir(parents=True, exist_ok=True)

    def crop(name, region):
        x, y, w, h = region
        file = f"{name}.png"
        if not cv2.imwrite(str(args.output / file), image[y : y + h, x : x + w]):
            raise OSError(f"Cannot write {file}")
        return {"file": file, "region": region}

    rules = {
        "resolution": [1920, 1080],
        "threshold": 0.94,
        "screens": {
            "HOME": [
                crop("attack", [55, 1000, 142, 40]),
                crop("shop", [1745, 1000, 107, 40]),
                crop("settings", [1800, 742, 80, 80]),
            ]
        },
        "account": crop("account", [147, 25, 90, 25]),
        "village_region": [300, 150, 1250, 730],
        "resources": [
            {"name": "gold", **crop("gold", [1065, 353, 44, 40])},
            {"name": "elixir", **crop("elixir", [918, 500, 42, 40])},
        ],
    }
    (args.output / "profile.json").write_text(
        json.dumps(rules, indent=2), encoding="utf-8"
    )


if __name__ == "__main__":
    main()
