"""Validate the single-track model against measurements of production cars.

    python scripts/validate_measured.py                    # all platforms below, downloads about 165 MB
    python scripts/validate_measured.py GENESIS_G70_2018   # one platform
    python scripts/validate_measured.py --data DIR         # zip files already downloaded to DIR

Data: commaSteeringControl (comma.ai, MIT license), https://huggingface.co/datasets/commaai/commaSteeringControl
Vehicle specifications: opendbc (comma.ai, MIT license), files opendbc/car/<brand>/values.py and interface.py.
Method and results: docs/validation/measured_data.md. Results are written to docs/validation/results.json.
"""

from __future__ import annotations

import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from vdsim.validation import PublicSpecs, compare, load_segments, vehicle_config  # noqa: E402

URL = "https://huggingface.co/datasets/commaai/commaSteeringControl/resolve/main/data/{}.zip"
# platform of the data set -> specifications as published in opendbc (wheelbase m, steering ratio,
# CoG position as share of the wheelbase from the front axle, tire stiffness factor)
PLATFORMS = {
    "GENESIS_G70_2018": PublicSpecs(wheelbase=2.84, steer_ratio=13.56, center_to_front_ratio=0.4),
    "KIA_SELTOS_2021": PublicSpecs(wheelbase=2.63, steer_ratio=14.56, center_to_front_ratio=0.4),
    "KIA_STINGER_2022": PublicSpecs(wheelbase=2.78, steer_ratio=14.4 * 1.15, center_to_front_ratio=0.4),
    "TOYOTA_C_HR_2018": PublicSpecs(wheelbase=2.63906, steer_ratio=13.6, center_to_front_ratio=0.44, tire_stiffness_factor=0.7933),
}


def main():
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("platforms", nargs="*", default=list(PLATFORMS))
    parser.add_argument("--data", type=Path, default=ROOT / "outputs" / "measured")
    parser.add_argument("--out", type=Path, default=ROOT / "docs" / "validation" / "results.json")
    args = parser.parse_args()
    args.data.mkdir(parents=True, exist_ok=True)
    results = {}
    for name in args.platforms:
        if name not in PLATFORMS:
            raise SystemExit(f"unknown platform {name}; known: {sorted(PLATFORMS)}")
        path = args.data / f"{name}.zip"
        if not path.exists():
            print(f"downloading {name} ...")
            urllib.request.urlretrieve(URL.format(name), path)  # noqa: S310 (fixed https URL)
        specs = PLATFORMS[name]
        r = compare(vehicle_config(specs), load_segments(path))
        results[name] = {"specs": {"wheelbase": specs.wheelbase, "steer_ratio": specs.steer_ratio,
                                   "center_to_front_ratio": specs.center_to_front_ratio,
                                   "tire_stiffness_factor": specs.tire_stiffness_factor}, **r}
        d, c, ref = r["dynamic"], r["dynamic_calibrated"], r["reference_model"]
        print(f"{name:20s} {r['hours']:5.1f} h  rms {r['measured_rms']:.2f} m/s^2   no fit: RMSE {d['rmse']:.3f} R2 {d['r2']:.3f}"
              f"   offset calibrated: RMSE {c['rmse']:.3f} R2 {c['r2']:.3f}   source model: RMSE {ref['rmse']:.3f} R2 {ref['r2']:.3f}")
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(results, indent=1) + "\n", encoding="utf-8")
    print(f"wrote {args.out.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
