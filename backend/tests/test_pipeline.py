import dataclasses

import numpy as np
import pytest

from pca.calibration import DarkSweep, MeterConfig, SpectralData, UnitCalibration
from pca.pipeline import (
    ABSOLUTE_SCALE,
    GridMismatchError,
    _scaled_dark,
    assert_compatible_grid,
    boxcar_smooth,
    modeled_dark,
    process,
)


def make_unit(n: int = 8) -> UnitCalibration:
    wavelengths = np.linspace(400.0, 700.0, n)
    dark = SpectralData(wavelengths, np.full(n, 100.0), 1_000_000)
    lamp = SpectralData(wavelengths, np.full(n, 2.0), 1_000_000)
    ref = SpectralData(wavelengths, np.zeros(n), 1_000_000)
    config = MeterConfig(
        boxcar=0, steradians=10.0, collection_area=1.0,
        agc_level=55_700, stable_tol=1_000, nl_correction=False, zero_candelas=0.0,
    )
    return UnitCalibration(dark, lamp, ref, config, dark_sweep=None)


def test_boxcar_identity_at_zero_half_width() -> None:
    values = np.array([1.0, 5.0, 3.0])
    assert np.array_equal(boxcar_smooth(values, 0), values)


def test_boxcar_averages_neighbours() -> None:
    values = np.array([0.0, 3.0, 6.0, 9.0, 12.0])
    smoothed = boxcar_smooth(values, 1)
    assert smoothed[2] == pytest.approx(6.0)
    assert smoothed[0] == pytest.approx(1.5)


def test_process_dark_and_scaling() -> None:
    unit = make_unit()
    raw = np.full(8, 600.0)
    radiance = process(raw, 500_000, unit)
    # dark scaled to 0.5s -> 50; net 550 counts in 0.5 s -> 1100 counts/s
    # * lamp 2.0 -> 2200; / delta-lambda (uniform 300/7 nm) -> 2200*7/300
    # -> 51.3333; / steradians 10 -> 5.13333; * ABSOLUTE_SCALE 1.0466 -> 5.372533...
    expected = 2200.0 / (300.0 / 7.0) / 10.0 * 1.0466
    assert radiance == pytest.approx(np.full(8, expected))


def test_process_clips_negative() -> None:
    unit = make_unit()
    radiance = process(np.zeros(8), 1_000_000, unit)
    assert np.all(radiance == 0.0)


def test_runtime_dark_overrides_stored() -> None:
    unit = make_unit()
    runtime_dark = SpectralData(unit.dark.wavelengths, np.full(8, 200.0), 500_000)
    raw = np.full(8, 600.0)
    radiance = process(raw, 500_000, unit, runtime_dark=runtime_dark)
    # net 400 counts in 0.5s -> 800/s * 2.0 -> 1600; / delta-lambda (300/7)
    # -> 1600*7/300; / steradians 10; * ABSOLUTE_SCALE 1.0466 -> 3.907487...
    expected = 1600.0 / (300.0 / 7.0) / 10.0 * 1.0466
    assert radiance == pytest.approx(np.full(8, expected))


def test_absolute_scale_is_calibrated_value() -> None:
    assert ABSOLUTE_SCALE == pytest.approx(1.0466)


def test_compatible_grid_accepts_the_calibrated_grid() -> None:
    unit = make_unit()
    assert_compatible_grid(unit.dark.wavelengths.copy(), unit)


def test_compatible_grid_tolerates_sub_tolerance_drift() -> None:
    unit = make_unit()
    assert_compatible_grid(unit.dark.wavelengths + 0.01, unit)


def test_compatible_grid_rejects_wrong_pixel_count() -> None:
    unit = make_unit()
    with pytest.raises(GridMismatchError, match="4 pixels"):
        assert_compatible_grid(np.linspace(400.0, 700.0, 4), unit)


def test_compatible_grid_rejects_same_length_foreign_grid() -> None:
    # The dangerous case: a different spectrometer with the same pixel count
    # broadcasts cleanly and would yield plausible but wrong radiance.
    unit = make_unit()
    foreign = np.linspace(340.0, 1030.0, unit.dark.wavelengths.size)
    with pytest.raises(GridMismatchError, match="nm"):
        assert_compatible_grid(foreign, unit)


def test_modeled_dark_interpolates_and_clamps() -> None:
    integs = np.array([10_000.0, 20_000.0])
    darks = np.array([np.full(4, 10.0), np.full(4, 30.0)])
    unit = dataclasses.replace(make_unit(), dark_sweep=DarkSweep(integs, darks))
    assert modeled_dark(15_000, unit) == pytest.approx(np.full(4, 20.0))  # midpoint
    assert modeled_dark(5_000, unit) == pytest.approx(np.full(4, 10.0))  # below -> first
    assert modeled_dark(50_000, unit) == pytest.approx(np.full(4, 30.0))  # above -> last


def test_modeled_dark_falls_back_to_scaled_dark_when_no_sweep() -> None:
    unit = make_unit()
    assert unit.dark_sweep is None
    assert modeled_dark(500_000, unit) == pytest.approx(_scaled_dark(unit.dark, 500_000))


def test_non_uniform_grid_scales_inversely_with_pixel_spacing() -> None:
    # Narrow-spacing region (indices 0-2, delta-lambda=1 nm, via np.gradient
    # central differences) vs wide-spacing region (indices 4-7, delta-lambda=
    # 2 nm); index 3 sits on the transition and is skipped.
    wavelengths = np.array([400.0, 401.0, 402.0, 403.0, 405.0, 407.0, 409.0, 411.0])
    dark = SpectralData(wavelengths, np.zeros(8), 1_000_000)
    lamp = SpectralData(wavelengths, np.full(8, 1.0), 1_000_000)
    ref = SpectralData(wavelengths, np.zeros(8), 1_000_000)
    config = MeterConfig(
        boxcar=0, steradians=1.0, collection_area=1.0,
        agc_level=55_700, stable_tol=1_000, nl_correction=False, zero_candelas=0.0,
    )
    unit = UnitCalibration(dark, lamp, ref, config, dark_sweep=None)
    radiance = process(np.full(8, 100.0), 1_000_000, unit)
    # counts and lamp are uniform across bins, so output is proportional to
    # 1/delta-lambda; wide spacing is 2x narrow spacing -> narrow/wide == 2x
    assert radiance[0] / radiance[4] == pytest.approx(2.0)
    assert radiance[0] == pytest.approx(radiance[1])
    assert radiance[4] == pytest.approx(radiance[5])
    assert radiance[5] == pytest.approx(radiance[6])
