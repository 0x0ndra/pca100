"""GitHub release check and DMG download. Leaf module: stdlib + pca.__version__ only."""
import fnmatch
import json
import os
import shutil
import urllib.request
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pca

RELEASES_URL = "https://api.github.com/repos/0x0ndra/pca100/releases/latest"
USER_AGENT = f"PCA-100/{pca.__version__}"
DMG_NAME_PATTERN = "PCA-100-*.dmg"


@dataclass(frozen=True)
class UpdateInfo:
    current: str
    latest: str | None = None
    available: bool = False
    release_url: str | None = None
    error: str | None = None
    asset_url: str | None = None


def _open_url(url: str, timeout: float) -> Any:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    return urllib.request.urlopen(request, timeout=timeout)  # noqa: S310


def _fetch_latest_release(timeout: float) -> bytes:
    with _open_url(RELEASES_URL, timeout) as response:
        return bytes(response.read())


def _semver(version: str) -> tuple[int, ...]:
    return tuple(int(x) for x in version.lstrip("v").split("."))


def _dmg_asset_url(assets: list[dict[str, Any]]) -> str | None:
    for asset in assets:
        name = asset.get("name", "")
        if fnmatch.fnmatch(name, DMG_NAME_PATTERN):
            url = asset.get("browser_download_url")
            return str(url) if url else None
    return None


def check_latest(timeout: float = 5.0) -> UpdateInfo:
    current = pca.__version__
    if os.environ.get("PCA_NO_UPDATE_CHECK"):
        return UpdateInfo(current=current, available=False, error=None)
    try:
        payload = json.loads(_fetch_latest_release(timeout))
        tag = str(payload["tag_name"])
        latest = tag.lstrip("v")
        available = _semver(latest) > _semver(current)
        return UpdateInfo(
            current=current,
            latest=latest,
            available=available,
            release_url=payload.get("html_url"),
            error=None,
            asset_url=_dmg_asset_url(payload.get("assets", [])),
        )
    except Exception as exc:  # network, JSON, or malformed-tag failures alike
        return UpdateInfo(current=current, available=False, error=f"{type(exc).__name__}: {exc}")


def download_dmg(asset_url: str, dest_dir: Path | None = None) -> Path:
    filename = asset_url.rsplit("/", 1)[-1]
    if not fnmatch.fnmatch(filename, DMG_NAME_PATTERN):
        raise ValueError(f"refusing to download non-PCA-100 asset: {filename}")
    target_dir = dest_dir if dest_dir is not None else Path.home() / "Downloads"
    target_dir.mkdir(parents=True, exist_ok=True)
    dest = target_dir / filename
    with _open_url(asset_url, 30.0) as response, dest.open("wb") as out:
        shutil.copyfileobj(response, out)
    return dest
