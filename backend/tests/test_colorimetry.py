import numpy as np
import pytest
from colour import SpectralShape, sd_blackbody

from pca.colorimetry import CDM2_PER_FTL, spectrum_to_reading


def test_blackbody_2856k_matches_illuminant_a() -> None:
    wavelengths = np.arange(340.0, 1029.0, 0.5)
    sd = sd_blackbody(2856.0, SpectralShape(340, 1028.5, 0.5))
    reading = spectrum_to_reading(wavelengths, sd.values)
    assert reading.x == pytest.approx(0.4476, abs=0.002)
    assert reading.y == pytest.approx(0.4074, abs=0.002)
    assert reading.cct_k == pytest.approx(2856, abs=30)
    assert abs(reading.duv) < 0.003


def test_flat_spectrum_absolute_luminance() -> None:
    wavelengths = np.arange(380.0, 781.0, 1.0)
    radiance = np.full_like(wavelengths, 0.01)
    reading = spectrum_to_reading(wavelengths, radiance)
    assert reading.luminance_cdm2 == pytest.approx(683 * 0.01 * 106.86, rel=0.01)
    assert reading.luminance_ftl == pytest.approx(reading.luminance_cdm2 / CDM2_PER_FTL)


def test_zero_spectrum_is_zero_luminance() -> None:
    wavelengths = np.arange(380.0, 781.0, 1.0)
    reading = spectrum_to_reading(wavelengths, np.zeros_like(wavelengths))
    assert reading.luminance_cdm2 == 0.0
