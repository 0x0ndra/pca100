"""Parsers for USL/SpectraSuite calibration files of one PCA-100 unit."""
import configparser
import json
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import numpy.typing as npt

_PAIR = re.compile(r"^(-?\d+(?:\.\d+)?)\t(-?\d+(?:\.\d+)?(?:E-?\d+)?)$", re.IGNORECASE)


@dataclass(frozen=True)
class SpectralData:
    wavelengths: npt.NDArray[np.float64]
    values: npt.NDArray[np.float64]
    integration_us: int


@dataclass(frozen=True)
class MeterConfig:
    boxcar: int
    steradians: float
    collection_area: float
    agc_level: int
    stable_tol: int
    nl_correction: bool
    zero_candelas: float


@dataclass(frozen=True)
class DarkSweep:
    integrations_us: npt.NDArray[np.float64]
    darks: npt.NDArray[np.float64]


@dataclass(frozen=True)
class UnitCalibration:
    dark: SpectralData
    lamp: SpectralData
    reference: SpectralData
    config: MeterConfig
    dark_sweep: DarkSweep | None = None


def _read_pairs(lines: list[str]) -> tuple[npt.NDArray[np.float64], npt.NDArray[np.float64]]:
    pairs = [m.groups() for line in lines if (m := _PAIR.match(line.strip()))]
    if not pairs:
        raise ValueError("no wavelength/value pairs found")
    data = np.array(pairs, dtype=np.float64)
    return data[:, 0], data[:, 1]


def _find_int(lines: list[str], pattern: str) -> int:
    regex = re.compile(pattern)
    for line in lines:
        if m := regex.search(line):
            return int(m.group(1))
    raise ValueError(f"header field not found: {pattern}")


def _require[T](value: T | None, field: str) -> T:
    if value is None:
        raise ValueError(f"missing INI field: {field}")
    return value


def parse_spectrasuite(path: Path) -> SpectralData:
    lines = path.read_text(encoding="latin-1").splitlines()
    integration_us = _find_int(lines, r"Integration Time \(usec\): (\d+)")
    wavelengths, values = _read_pairs(lines)
    return SpectralData(wavelengths, values, integration_us)


def parse_lamp(path: Path) -> SpectralData:
    lines = path.read_text(encoding="latin-1").splitlines()
    integration_us = _find_int(lines, r"Int\. Time \(usec\)\t(\d+)")
    wavelengths, values = _read_pairs(lines)
    return SpectralData(wavelengths, values, integration_us)


def parse_colormeter_ini(path: Path) -> MeterConfig:
    parser = configparser.ConfigParser()
    parser.read_string(path.read_text(encoding="latin-1"))
    section = parser["Parameters"]
    return MeterConfig(
        boxcar=_require(section.getint("Boxcar"), "Boxcar"),
        steradians=_require(section.getfloat("Steradians"), "Steradians"),
        collection_area=_require(section.getfloat("CollectionArea"), "CollectionArea"),
        agc_level=_require(section.getint("AGCLevel"), "AGCLevel"),
        stable_tol=_require(section.getint("StableTol"), "StableTol"),
        nl_correction=_require(section.getboolean("NLCorrection"), "NLCorrection"),
        zero_candelas=_require(section.getfloat("ZeroCandellas"), "ZeroCandellas"),
    )


def parse_dark_sweep(
    path: Path, reference_wavelengths: npt.NDArray[np.float64] | None = None
) -> DarkSweep:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if reference_wavelengths is not None and "wavelengths" in payload:
        sweep_wavelengths = np.asarray(payload["wavelengths"], dtype=np.float64)
        if not np.allclose(sweep_wavelengths, reference_wavelengths, atol=0.05):
            raise ValueError("dark_sweep wavelengths do not match unit dark grid")
    integrations = sorted(int(t) for t in payload["integrations_us"])
    darks_rows = [payload["darks"][str(t)] for t in integrations]
    if reference_wavelengths is not None:
        expected_len = len(reference_wavelengths)
    elif "wavelengths" in payload:
        expected_len = len(payload["wavelengths"])
    else:
        expected_len = len(darks_rows[0])
    for t, row in zip(integrations, darks_rows, strict=True):
        if len(row) != expected_len:
            raise ValueError(
                f"dark_sweep row for integration {t}us has {len(row)} values, "
                f"expected {expected_len}"
            )
    darks = np.array(darks_rows, dtype=np.float64)
    return DarkSweep(np.asarray(integrations, dtype=np.float64), darks)


def load_unit(data_dir: Path) -> UnitCalibration:
    dark = parse_spectrasuite(data_dir / "dark.bin")
    sweep_path = data_dir / "dark_sweep.json"
    dark_sweep = (
        parse_dark_sweep(sweep_path, dark.wavelengths) if sweep_path.exists() else None
    )
    return UnitCalibration(
        dark=dark,
        lamp=parse_lamp(data_dir / "lamp.bin"),
        reference=parse_spectrasuite(data_dir / "reference.bin"),
        config=parse_colormeter_ini(data_dir / "colormeter.ini"),
        dark_sweep=dark_sweep,
    )
