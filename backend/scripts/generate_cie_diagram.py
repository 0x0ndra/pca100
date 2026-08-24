"""Render the filled CIE 1931 chromaticity horseshoe to a PNG for the frontend."""

from pathlib import Path

import colour
import numpy as np
from numpy.typing import NDArray
from PIL import Image

SIZE = 600
DOMAIN_X = 0.8
DOMAIN_Y = 0.9


def chromaticity_grid() -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """xy chromaticity for each pixel, matching xyToSvg with preserveAspectRatio=none."""
    cols = np.arange(SIZE)
    rows = np.arange(SIZE)
    x = DOMAIN_X * cols / (SIZE - 1)
    y = DOMAIN_Y * (1.0 - rows / (SIZE - 1))
    return np.meshgrid(x, y)


def vivid_srgb(xx: NDArray[np.float64], yy: NDArray[np.float64]) -> NDArray[np.float64]:
    """Full-brightness sRGB for each chromaticity (MacAdam-style fill)."""
    safe_y = np.where(yy > 0.0, yy, 1.0)
    big_x = xx / safe_y
    big_z = (1.0 - xx - yy) / safe_y
    xyz = np.stack([big_x, np.ones_like(xx), big_z], axis=-1)
    linear = colour.XYZ_to_sRGB(xyz, apply_cctf_encoding=False)
    linear = np.clip(linear, 0.0, None)
    peak = np.max(linear, axis=-1, keepdims=True)
    linear = np.divide(linear, peak, out=np.zeros_like(linear), where=peak > 0.0)
    return np.asarray(colour.cctf_encoding(linear, function="sRGB"), dtype=np.float64)


def locus_polygon() -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    """Spectral-locus boundary vertices (monochromatic xy, closed via the purple line)."""
    cmfs = colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]
    xs: list[float] = []
    ys: list[float] = []
    for nm in range(360, 701):
        tri = cmfs[float(nm)]
        total = float(tri[0] + tri[1] + tri[2])
        if total <= 0.0:
            continue
        xs.append(float(tri[0]) / total)
        ys.append(float(tri[1]) / total)
    return np.array(xs), np.array(ys)


def points_in_polygon(
    px: NDArray[np.float64],
    py: NDArray[np.float64],
    vx: NDArray[np.float64],
    vy: NDArray[np.float64],
) -> NDArray[np.bool_]:
    """Vectorized even-odd ray-cast: True where (px, py) is inside the polygon."""
    inside = np.zeros(px.shape, dtype=bool)
    prev = len(vx) - 1
    with np.errstate(divide="ignore", invalid="ignore"):
        for curr in range(len(vx)):
            yi, yj = vy[curr], vy[prev]
            straddles = (yi > py) != (yj > py)
            x_cross = (vx[prev] - vx[curr]) * (py - yi) / (yj - yi) + vx[curr]
            inside ^= straddles & (px < x_cross)
            prev = curr
    return inside


def build_rgba() -> NDArray[np.uint8]:
    xx, yy = chromaticity_grid()
    rgb = vivid_srgb(xx, yy)
    vx, vy = locus_polygon()
    mask = points_in_polygon(xx, yy, vx, vy) & (yy > 0.0)
    rgba = np.zeros((SIZE, SIZE, 4), dtype=np.uint8)
    rgba[..., :3] = np.clip(rgb * 255.0 + 0.5, 0, 255).astype(np.uint8)
    rgba[..., 3] = np.where(mask, 255, 0).astype(np.uint8)
    return rgba


def main() -> None:
    out = Path(__file__).parents[2] / "frontend" / "public" / "cie-chromaticity.png"
    Image.fromarray(build_rgba(), "RGBA").save(out)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
