from pathlib import Path

import pytest

import pca
import pca.updater
from pca.engine import DownloadState
from tests.test_api import HOSTILE_ORIGIN, make_client


def test_get_update_reports_current_version(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    body = client.get("/api/update").json()
    assert body["current"] == pca.__version__
    assert body["download"] == {"state": "idle", "error": None, "path": None}


def test_post_update_download_runs_and_opens_dmg(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    dmg_path = tmp_path / "PCA-100-1.2.0.dmg"
    dmg_path.write_bytes(b"fake dmg")
    monkeypatch.setattr(
        "pca.api_update.updater.download_dmg", lambda asset_url, dest_dir=None: dmg_path
    )
    open_calls = []
    monkeypatch.setattr("pca.api_update.subprocess.run", lambda args, **kw: open_calls.append(args))
    client = make_client(tmp_path)
    client.app.state.app_state.update_info = pca.updater.UpdateInfo(
        current="1.1.0",
        latest="1.2.0",
        available=True,
        asset_url="https://example.com/PCA-100-1.2.0.dmg",
    )
    response = client.post("/api/update/download")
    assert response.status_code == 200
    body = client.get("/api/update").json()
    assert body["download"]["state"] == "downloaded"
    assert body["download"]["path"] == str(dmg_path)
    assert open_calls == [["open", str(dmg_path)]]


def test_post_update_download_without_asset_url_returns_current_state(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.post("/api/update/download")
    assert response.status_code == 200
    assert response.json()["download"]["state"] == "idle"


def test_post_update_download_records_error_state(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def _fail(asset_url: str, dest_dir: Path | None = None) -> Path:
        raise ValueError("bad dmg")

    monkeypatch.setattr("pca.api_update.updater.download_dmg", _fail)
    client = make_client(tmp_path)
    client.app.state.app_state.update_info = pca.updater.UpdateInfo(
        current="1.1.0", asset_url="https://example.com/evil.dmg"
    )
    client.post("/api/update/download")
    body = client.get("/api/update").json()
    assert body["download"]["state"] == "error"
    assert body["download"]["error"] is not None


def test_post_update_download_while_downloading_does_not_start_second_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls: list[str] = []

    def _slow_download(asset_url: str, dest_dir: Path | None = None) -> Path:
        calls.append(asset_url)
        return tmp_path / "PCA-100-1.2.0.dmg"

    monkeypatch.setattr("pca.api_update.updater.download_dmg", _slow_download)
    client = make_client(tmp_path)
    client.app.state.app_state.update_info = pca.updater.UpdateInfo(
        current="1.1.0",
        latest="1.2.0",
        available=True,
        asset_url="https://example.com/PCA-100-1.2.0.dmg",
    )
    client.app.state.app_state.download = DownloadState(state="downloading")

    response = client.post("/api/update/download")

    assert response.status_code == 200
    assert response.json()["download"]["state"] == "downloading"
    assert calls == []


def test_hostile_origin_cannot_trigger_download(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.post("/api/update/download", headers=HOSTILE_ORIGIN)
    assert response.status_code == 403
