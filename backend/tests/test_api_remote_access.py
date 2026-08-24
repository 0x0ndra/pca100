import json
from pathlib import Path

import pytest

import pca.settings
from tests.test_api import make_client


def test_remote_access_get_defaults_disabled(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pca.settings, "_SETTINGS_PATH", tmp_path / "settings.json")
    client = make_client(tmp_path)
    body = client.get("/api/remote-access").json()
    assert body == {"enabled": False, "urls": [], "qr": None}


def test_remote_access_post_enables_returns_urls_and_qr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pca.settings, "_SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr("pca.api.netguard.local_ipv4s", lambda: frozenset({"192.168.1.20"}))
    client = make_client(tmp_path)
    body = client.post("/api/remote-access", json={"enabled": True}).json()
    assert body["enabled"] is True
    assert body["urls"] == ["http://192.168.1.20:8320"]
    assert body["qr"].startswith("data:image/png;base64,")
    assert client.app.state.app_state.remote_access is True


def test_remote_access_post_disables_returns_empty_urls_and_no_qr(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pca.settings, "_SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr("pca.api.netguard.local_ipv4s", lambda: frozenset({"192.168.1.20"}))
    client = make_client(tmp_path, remote_access=True)
    body = client.post("/api/remote-access", json={"enabled": False}).json()
    assert body == {"enabled": False, "urls": [], "qr": None}


def test_remote_access_post_persists_setting(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    settings_path = tmp_path / "settings.json"
    monkeypatch.setattr(pca.settings, "_SETTINGS_PATH", settings_path)
    client = make_client(tmp_path)
    client.post("/api/remote-access", json={"enabled": True})
    assert json.loads(settings_path.read_text())["remote_access"] is True


def test_remote_access_post_calls_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(pca.settings, "_SETTINGS_PATH", tmp_path / "settings.json")
    calls: list[bool] = []
    client = make_client(tmp_path, on_remote_access_change=calls.append)
    client.post("/api/remote-access", json={"enabled": True})
    assert calls == [True]
