"""Acceptance check: reconciled dark-model pipeline vs original app (unit 0302).

Runs the four captured MacBook-P3 validation patches through the real
process() + spectrum_to_reading() and prints x / y / luminance against the
known original-app values.
"""
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pca.calibration import load_unit
from pca.colorimetry import spectrum_to_reading
from pca.pipeline import process

DATA = Path(__file__).resolve().parent.parent / "data"
# patch -> original-app x, y, luminance (ft-L)
REFERENCE = {
    "white": (0.313, 0.323, 130.5),
    "red": (0.676, 0.319, 30.9),
    "green": (0.266, 0.691, 89.0),
    "blue": (0.152, 0.059, 10.5),
}


def main() -> None:
    unit = load_unit(DATA / "0302")
    header = f"{'patch':6} {'x':>7} {'y':>7} {'ftL':>7}   {'ref x / y / ftL'}"
    print(header)
    print("-" * len(header))
    for name, (rx, ry, rl) in REFERENCE.items():
        payload = json.loads((DATA / "validation" / f"patch_mbp_{name}.json").read_text())
        raw = np.asarray(payload["raw_mean"], dtype=np.float64)
        wavelengths = np.asarray(payload["wavelengths"], dtype=np.float64)
        integration_us = int(payload["integration_us"])
        spectrum = process(raw, integration_us, unit)
        reading = spectrum_to_reading(wavelengths, spectrum)
        print(
            f"{name:6} {reading.x:7.3f} {reading.y:7.3f} {reading.luminance_ftl:7.1f}"
            f"   {rx:.3f} / {ry:.3f} / {rl}"
        )


if __name__ == "__main__":
    main()
