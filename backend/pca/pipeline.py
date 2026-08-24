"""Raw spectrometer counts -> absolute spectral radiance."""
import numpy as np
import numpy.typing as npt

from pca.calibration import SpectralData, UnitCalibration

# Re-derived 2026-07-24 with the measured dark model (see modeled_dark), unit
# 0302, MacBook P3 white patch: old app 130.5 ft-L / our raw ~124.7 ft-L =
# 1.0466. The prior value 1.031318 assumed the linearly-scaled 2009 dark.bin.
ABSOLUTE_SCALE: float = 1.0466

GRID_TOLERANCE_NM = 0.05


class GridMismatchError(RuntimeError):
    pass


def assert_compatible_grid(
    wavelengths: npt.NDArray[np.float64], unit: UnitCalibration
) -> None:
    """Reject a device whose pixel grid is not the one this unit was calibrated on.

    process() subtracts the stored dark and multiplies by the stored lamp
    element-wise. A different spectrometer with the same pixel count would
    broadcast cleanly and yield plausible-looking but wrong radiance, so the
    grid has to be verified before any measurement is trusted.
    """
    expected = unit.dark.wavelengths
    if wavelengths.shape != expected.shape:
        raise GridMismatchError(
            f"device reports {wavelengths.size} pixels, calibration has {expected.size}"
        )
    if not np.allclose(wavelengths, expected, atol=GRID_TOLERANCE_NM):
        worst = float(np.max(np.abs(wavelengths - expected)))
        raise GridMismatchError(
            f"device wavelength grid differs from calibration by up to {worst:.2f} nm"
        )


def boxcar_smooth(
    values: npt.NDArray[np.float64], half_width: int
) -> npt.NDArray[np.float64]:
    if half_width <= 0:
        return values.copy()
    window = 2 * half_width + 1
    kernel = np.ones(window) / window
    padded = np.convolve(values, kernel, mode="same")
    norm = np.convolve(np.ones_like(values), kernel, mode="same")
    return padded / norm


def _scaled_dark(
    dark: SpectralData, integration_us: int
) -> npt.NDArray[np.float64]:
    return dark.values * (integration_us / dark.integration_us)


def modeled_dark(
    integration_us: int, unit: UnitCalibration
) -> npt.NDArray[np.float64]:
    sweep = unit.dark_sweep
    if sweep is None:
        return _scaled_dark(unit.dark, integration_us)
    integs = sweep.integrations_us
    if integration_us <= integs[0]:
        return np.asarray(sweep.darks[0], dtype=np.float64)
    if integration_us >= integs[-1]:
        return np.asarray(sweep.darks[-1], dtype=np.float64)
    hi = int(np.searchsorted(integs, integration_us))
    lo = hi - 1
    frac = (integration_us - integs[lo]) / (integs[hi] - integs[lo])
    interpolated = sweep.darks[lo] + frac * (sweep.darks[hi] - sweep.darks[lo])
    return np.asarray(interpolated, dtype=np.float64)


def process(
    raw_counts: npt.NDArray[np.float64],
    integration_us: int,
    unit: UnitCalibration,
    runtime_dark: SpectralData | None = None,
) -> npt.NDArray[np.float64]:
    if runtime_dark is not None:
        dark_spectrum = _scaled_dark(runtime_dark, integration_us)
    else:
        dark_spectrum = modeled_dark(integration_us, unit)
    net = raw_counts - dark_spectrum
    net = boxcar_smooth(net, unit.config.boxcar)
    counts_per_s = net / (integration_us / 1e6)
    radiance = counts_per_s * unit.lamp.values
    radiance /= np.gradient(unit.dark.wavelengths)
    radiance /= unit.config.steradians * unit.config.collection_area
    radiance *= ABSOLUTE_SCALE
    return np.clip(radiance, 0.0, None)
