"""Parser tests against synthetic fixtures in the real file formats.

The actual calibration of a unit is personal to that instrument and is not
shipped in the repository, so these tests generate minimal files in the
SpectraSuite / lamp / INI / dark-sweep formats instead.
"""
import json
from pathlib import Path

import numpy as np
import pytest

from pca.calibration import (
    load_unit,
    parse_colormeter_ini,
    parse_dark_sweep,
    parse_lamp,
    parse_spectrasuite,
)

WAVELENGTHS = [339.68, 340.05, 340.42, 340.79]

INI_TEXT = """[Parameters]
Boxcar=5
Steradians=2.102029E4
CollectionArea=1.0
AGCLevel=55700
StableTol=1000
NLCorrection=1
chromacorrection=0
ZeroCandellas=0.0
"""


def _pairs(values: list[float]) -> str:
    return "\n".join(f"{w}\t{v}" for w, v in zip(WAVELENGTHS, values, strict=True))


def _write_spectrasuite(path: Path, values: list[float], integration_us: int) -> None:
    path.write_text(
        "SpectraSuite Data File\n"
        f"Integration Time (usec): {integration_us} (USB2000+)\n"
        ">>>>>Begin Processed Spectral Data<<<<<\n"
        f"{_pairs(values)}\n"
        ">>>>>End Processed Spectral Data<<<<<\n",
        encoding="latin-1",
    )


def _write_lamp(path: Path, values: list[float], integration_us: int) -> None:
    path.write_text(
        f"Int. Time (usec)\t{integration_us}\n{_pairs(values)}\n",
        encoding="latin-1",
    )


def _write_dark_sweep(path: Path, integrations_us: list[int]) -> None:
    payload = {
        "wavelengths": WAVELENGTHS,
        "integrations_us": integrations_us,
        "darks": {str(t): [float(i)] * len(WAVELENGTHS) for i, t in enumerate(integrations_us)},
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def _write_unit(data_dir: Path, with_sweep: bool = True) -> None:
    _write_spectrasuite(data_dir / "dark.bin", [-115.431, -114.0, -113.5, -115.0], 1_575_000)
    _write_spectrasuite(data_dir / "reference.bin", [-114.233, -113.9, -112.7, -114.8], 1_575_000)
    _write_lamp(data_dir / "lamp.bin", [1.2e-5, 1.3e-5, 1.4e-5, 1.5e-5], 1_575_000_000)
    (data_dir / "colormeter.ini").write_text(INI_TEXT, encoding="latin-1")
    if with_sweep:
        _write_dark_sweep(data_dir / "dark_sweep.json", [3000, 20_000, 100_000, 1_000_000])


def test_parse_dark(tmp_path: Path) -> None:
    _write_spectrasuite(tmp_path / "dark.bin", [-115.431, -114.0, -113.5, -115.0], 1_575_000)
    dark = parse_spectrasuite(tmp_path / "dark.bin")
    assert dark.wavelengths.shape == (4,)
    assert dark.values.shape == (4,)
    assert dark.integration_us == 1_575_000
    assert dark.wavelengths[0] == pytest.approx(339.68)
    assert dark.wavelengths[-1] == pytest.approx(340.79)
    assert dark.values[0] == pytest.approx(-115.431)
    assert np.all(np.diff(dark.wavelengths) > 0)


def test_parse_spectrasuite_rejects_file_without_pairs(tmp_path: Path) -> None:
    (tmp_path / "empty.bin").write_text(
        "SpectraSuite Data File\nIntegration Time (usec): 1000 (USB2000+)\n",
        encoding="latin-1",
    )
    with pytest.raises(ValueError, match="no wavelength/value pairs"):
        parse_spectrasuite(tmp_path / "empty.bin")


def test_parse_lamp(tmp_path: Path) -> None:
    _write_lamp(tmp_path / "lamp.bin", [1.2e-5, 1.3e-5, 1.4e-5, 1.5e-5], 1_575_000_000)
    lamp = parse_lamp(tmp_path / "lamp.bin")
    assert lamp.wavelengths.shape == (4,)
    assert lamp.integration_us == 1_575_000_000
    assert lamp.values[0] == pytest.approx(1.2e-5)
    assert np.all(np.isfinite(lamp.values))


def test_parse_ini(tmp_path: Path) -> None:
    (tmp_path / "colormeter.ini").write_text(INI_TEXT, encoding="latin-1")
    config = parse_colormeter_ini(tmp_path / "colormeter.ini")
    assert config.boxcar == 5
    assert config.steradians == pytest.approx(2.102029e4)
    assert config.agc_level == 55_700
    assert config.stable_tol == 1_000
    assert config.nl_correction is True
    assert config.zero_candelas == pytest.approx(0.0)


def test_parse_ini_missing_field_raises(tmp_path: Path) -> None:
    (tmp_path / "colormeter.ini").write_text("[Parameters]\nBoxcar=5\n", encoding="latin-1")
    with pytest.raises(ValueError, match="missing INI field"):
        parse_colormeter_ini(tmp_path / "colormeter.ini")


def test_load_unit(tmp_path: Path) -> None:
    _write_unit(tmp_path)
    unit = load_unit(tmp_path)
    assert unit.config.boxcar == 5
    assert unit.dark.values.shape == unit.lamp.values.shape


def test_load_unit_without_sweep(tmp_path: Path) -> None:
    _write_unit(tmp_path, with_sweep=False)
    assert load_unit(tmp_path).dark_sweep is None


def test_parse_dark_sweep(tmp_path: Path) -> None:
    _write_dark_sweep(tmp_path / "dark_sweep.json", [3000, 20_000, 100_000, 1_000_000])
    sweep = parse_dark_sweep(tmp_path / "dark_sweep.json")
    assert sweep.darks.shape == (4, 4)
    assert sweep.integrations_us.shape == (4,)
    assert sweep.integrations_us[0] == pytest.approx(3000.0)
    assert sweep.integrations_us[-1] == pytest.approx(1_000_000.0)
    assert np.all(np.diff(sweep.integrations_us) > 0)


def test_parse_dark_sweep_rejects_mismatched_grid(tmp_path: Path) -> None:
    _write_dark_sweep(tmp_path / "dark_sweep.json", [3000, 20_000])
    shifted = np.asarray(WAVELENGTHS) + 1.0
    with pytest.raises(ValueError, match="do not match"):
        parse_dark_sweep(tmp_path / "dark_sweep.json", shifted)


def test_parse_dark_sweep_rejects_short_row_without_wavelengths(tmp_path: Path) -> None:
    payload = {
        "integrations_us": [3000, 20_000],
        "darks": {"3000": [1.0, 1.0, 1.0, 1.0], "20000": [1.0, 1.0]},
    }
    path = tmp_path / "dark_sweep.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    with pytest.raises(ValueError, match="dark_sweep row"):
        parse_dark_sweep(path)


def test_load_unit_has_dark_sweep(tmp_path: Path) -> None:
    _write_unit(tmp_path)
    unit = load_unit(tmp_path)
    assert unit.dark_sweep is not None
    assert unit.dark_sweep.darks.shape == (4, 4)
    assert np.all(np.diff(unit.dark_sweep.integrations_us) > 0)
