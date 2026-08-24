"""Persisted application settings (JSON in Application Support). Bottom layer."""
import json
from pathlib import Path
from typing import Any

_SETTINGS_PATH = Path.home() / "Library" / "Application Support" / "PCA-100" / "settings.json"


def settings_path() -> Path:
    return _SETTINGS_PATH


def _read() -> dict[str, Any]:
    try:
        content = json.loads(_SETTINGS_PATH.read_text())
        if isinstance(content, dict):
            return content
        return {}
    except (OSError, ValueError):
        return {}


def get_remote_access() -> bool:
    return bool(_read().get("remote_access", False))


def set_remote_access(enabled: bool) -> None:
    data = _read()
    data["remote_access"] = bool(enabled)
    _SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    _SETTINGS_PATH.write_text(json.dumps(data, indent=2))
