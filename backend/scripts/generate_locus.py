"""Generate CIE 1931 spectral locus xy pairs for the frontend diagram."""
import json
from pathlib import Path

import colour

cmfs = colour.MSDS_CMFS["CIE 1931 2 Degree Standard Observer"]
pairs = []
for nm in range(380, 701, 2):
    xyz = cmfs[float(nm)]
    total = float(xyz[0] + xyz[1] + xyz[2])
    pairs.append([round(float(xyz[0]) / total, 5), round(float(xyz[1]) / total, 5)])

out = Path(__file__).parents[2] / "frontend" / "src" / "lib" / "spectral-locus.json"
out.write_text(json.dumps(pairs))
