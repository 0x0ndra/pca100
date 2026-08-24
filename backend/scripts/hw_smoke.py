"""Manual hardware check: connect the real PCA-100 and print live readings."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pca.calibration import load_unit
from pca.device import open_first_available
from pca.engine import Engine, Measurement

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "0302"
MEASUREMENT_COUNT = 3


def _format_measurement(measurement: Measurement) -> str:
    reading = measurement.reading
    return (
        f"jas: {reading.luminance_ftl:.3f} ft-L / {reading.luminance_cdm2:.3f} cd/m2 | "
        f"x={reading.x:.4f} y={reading.y:.4f} | CCT={reading.cct_k:.0f} K | "
        f"integrace={measurement.integration_us / 1000:.1f} ms | "
        f"stabilni={measurement.stable} saturace={measurement.saturated}"
    )


def main() -> int:
    unit = load_unit(DATA_DIR)
    engine = Engine(unit, connect=open_first_available)
    if not engine.ensure_connected():
        print("PCA-100 nenalezen - zkontroluj USB pripojeni.", file=sys.stderr)
        return 1

    print(f"Seriove cislo: {engine.serial}")
    for i in range(1, MEASUREMENT_COUNT + 1):
        measurement = engine.measure_once()
        print(f"{i}. {_format_measurement(measurement)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
