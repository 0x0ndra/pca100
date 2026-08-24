"""Spectral radiance to CIE 1931 colorimetric quantities."""
from dataclasses import dataclass

import colour
import numpy as np
import numpy.typing as npt

CDM2_PER_FTL = 3.4262591
_CMFS = colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]
_SHAPE = colour.SpectralShape(380, 780, 1)


@dataclass(frozen=True)
class ColorReading:
    x: float
    y: float
    luminance_cdm2: float
    luminance_ftl: float
    cct_k: float
    duv: float


def spectrum_to_reading(
    wavelengths: npt.NDArray[np.float64], radiance: npt.NDArray[np.float64]
) -> ColorReading:
    paired = zip(wavelengths.tolist(), radiance.tolist(), strict=True)
    sd = colour.SpectralDistribution(dict(paired))
    sd = sd.align(_SHAPE)
    xyz = colour.sd_to_XYZ(sd, cmfs=_CMFS, method="Integration", k=683, strict=False)
    luminance_cdm2 = float(xyz[1])
    if luminance_cdm2 <= 0.0:
        return ColorReading(0.0, 0.0, 0.0, 0.0, 0.0, 0.0)
    xy = colour.XYZ_to_xy(xyz)
    uv = colour.UCS_to_uv(colour.XYZ_to_UCS(xyz))
    cct_k, duv = (float(v) for v in colour.temperature.uv_to_CCT_Ohno2013(uv))
    return ColorReading(
        x=float(xy[0]),
        y=float(xy[1]),
        luminance_cdm2=luminance_cdm2,
        luminance_ftl=luminance_cdm2 / CDM2_PER_FTL,
        cct_k=cct_k,
        duv=duv,
    )
