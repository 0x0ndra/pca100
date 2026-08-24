"""Resolve calibration (user data) and frontend paths for dev and frozen runs."""
import sys
from pathlib import Path

_CALIBRATION_DIR = Path.home() / "Library" / "Application Support" / "PCA-100" / "calibration"
_REQUIRED = ("dark.bin", "lamp.bin", "reference.bin", "colormeter.ini")
_BACKEND_ROOT = Path(__file__).resolve().parent.parent
_REPO_ROOT = _BACKEND_ROOT.parent


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def calibration_dir() -> Path:
    _CALIBRATION_DIR.mkdir(parents=True, exist_ok=True)
    return _CALIBRATION_DIR


def calibration_present() -> bool:
    return all((_CALIBRATION_DIR / name).exists() for name in _REQUIRED)


def resource_frontend_dir() -> Path:
    if is_frozen():
        return Path(sys._MEIPASS) / "frontend" / "dist"  # type: ignore[attr-defined]
    return _REPO_ROOT / "frontend" / "dist"
