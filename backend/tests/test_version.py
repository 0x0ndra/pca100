import tomllib
from pathlib import Path

import pca


def test_pyproject_matches_dunder_version() -> None:
    data = tomllib.loads((Path(pca.__file__).resolve().parents[1] / "pyproject.toml").read_text())
    assert data["project"]["version"] == pca.__version__
