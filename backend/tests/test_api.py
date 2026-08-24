from collections.abc import Callable
from pathlib import Path

import numpy as np
import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocketDisconnect

import pca
from pca.api import create_app
from pca.device import FakeSpectrometer
from pca.engine import AppState, Engine
from tests.test_engine import _fake_unit, _flat_spectrum, make_unit

N = 32
HOSTILE_ORIGIN = {"origin": "https://evil.example.com"}
LOCAL_ORIGIN = {"origin": "http://localhost:5175"}
LAN_ORIGIN = {"origin": "http://192.168.1.50:5175"}


def _client(app: FastAPI, base_url: str = "http://127.0.0.1") -> TestClient:
    # A real browser/OS sends a loopback Host by default; the DNS-rebinding
    # guard checks Host on every request, so tests must pin one explicitly
    # instead of the TestClient default ("http://testserver").
    return TestClient(app, base_url=base_url)


def _empty_state(tmp_path: Path) -> AppState:
    return AppState(engine=None, load_engine=lambda: None, calibration_dir=tmp_path)


def make_client(
    tmp_path: Path,
    remote_access: bool = False,
    on_remote_access_change: Callable[[bool], None] | None = None,
) -> TestClient:
    wavelengths = np.linspace(380.0, 780.0, N)
    device = FakeSpectrometer(wavelengths, [np.full(N, 30_000.0)])
    engine = Engine(make_unit(wavelengths), connect=lambda: device)
    engine.ensure_connected()
    state = AppState(
        engine=engine,
        load_engine=lambda: engine,
        calibration_dir=tmp_path,
        remote_access=remote_access,
        on_remote_access_change=on_remote_access_change,
    )
    return _client(create_app(state))


def test_status(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    body = client.get("/api/status").json()
    assert body["connected"] is True
    assert body["serial"] == "FAKE-0001"
    assert body["scanning"] is True
    assert body["averaging"] is True
    assert body["calibration_present"] is True


def test_status_reports_version(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    body = client.get("/api/status").json()
    assert body["version"] == pca.__version__


def test_status_without_calibration(tmp_path: Path) -> None:
    app = create_app(_empty_state(tmp_path))
    with _client(app) as client:
        body = client.get("/api/status").json()
    assert body["connected"] is False
    assert body["calibration_present"] is False


def test_scan_start_conflicts_without_engine(tmp_path: Path) -> None:
    app = create_app(_empty_state(tmp_path))
    with _client(app) as client:
        assert client.post("/api/scan/start").status_code == 409


def test_dark_and_averaging_conflict_without_engine(tmp_path: Path) -> None:
    app = create_app(_empty_state(tmp_path))
    with _client(app) as client:
        assert client.post("/api/dark").status_code == 409
        assert client.delete("/api/dark").status_code == 409
        assert client.post("/api/averaging", json={"enabled": True}).status_code == 409


def test_measurement_conflicts_without_engine(tmp_path: Path) -> None:
    app = create_app(_empty_state(tmp_path))
    with _client(app) as client:
        assert client.get("/api/measurement").status_code == 409


def test_reload_creates_engine(tmp_path: Path) -> None:
    unit = _fake_unit()
    state = AppState(
        engine=None,
        load_engine=lambda: Engine(
            unit, connect=lambda: FakeSpectrometer(unit.dark.wavelengths, [_flat_spectrum(unit)])
        ),
        calibration_dir=tmp_path,
    )
    app = create_app(state)
    with _client(app) as client:
        assert client.post("/api/calibration/reload").json()["calibration_present"] is True
        assert client.get("/api/status").json()["calibration_present"] is True


def test_reload_closes_old_engine_device(tmp_path: Path) -> None:
    unit = _fake_unit()
    old_device = FakeSpectrometer(unit.dark.wavelengths, [_flat_spectrum(unit)])
    close_calls = []
    old_device.close = lambda: close_calls.append(True)  # type: ignore[method-assign]
    old_engine = Engine(unit, connect=lambda: old_device)
    old_engine.ensure_connected()

    new_unit = _fake_unit()
    state = AppState(
        engine=old_engine,
        load_engine=lambda: Engine(
            new_unit,
            connect=lambda: FakeSpectrometer(new_unit.dark.wavelengths, [_flat_spectrum(new_unit)]),
        ),
        calibration_dir=tmp_path,
    )
    app = create_app(state)
    with _client(app) as client:
        body = client.post("/api/calibration/reload").json()
    assert body["calibration_present"] is True
    assert close_calls == [True]


def test_reveal_calibration_opens_directory(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    calls = []
    monkeypatch.setattr("pca.api.subprocess.run", lambda args, **kw: calls.append(args))
    app = create_app(_empty_state(tmp_path))
    with _client(app) as client:
        assert client.post("/api/calibration/reveal").json()["ok"] is True
    assert calls == [["open", str(tmp_path)]]


def test_serves_frontend_when_dir_exists(tmp_path: Path) -> None:
    frontend_dir = tmp_path / "frontend"
    frontend_dir.mkdir()
    (frontend_dir / "index.html").write_text("<html>PCA</html>")
    app = create_app(_empty_state(tmp_path), frontend_dir=frontend_dir)
    with _client(app) as client:
        response = client.get("/")
    assert response.status_code == 200
    assert "PCA" in response.text


def test_no_frontend_mount_when_dir_missing(tmp_path: Path) -> None:
    app = create_app(_empty_state(tmp_path), frontend_dir=tmp_path / "missing")
    with _client(app) as client:
        response = client.get("/")
    assert response.status_code == 404


def test_averaging_toggle(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    assert client.post("/api/averaging", json={"enabled": False}).json()["averaging"] is False
    assert client.app.state.app_state.engine.averaging is False
    assert client.post("/api/averaging", json={"enabled": True}).json()["averaging"] is True


def test_status_reflects_disconnected_engine(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.app.state.app_state.engine.connected = False
    body = client.get("/api/status").json()
    assert body["connected"] is False


def test_measurement_404_then_ok(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    assert client.get("/api/measurement").status_code == 404
    client.app.state.app_state.engine.measure_once()
    body = client.get("/api/measurement").json()
    assert body["x"] > 0 and body["luminance_cdm2"] > 0
    assert body["stability"] == "acquiring"
    assert body["variation_pct"] == 0.0
    assert "spectrum" not in body
    with_spectrum = client.get("/api/measurement", params={"spectrum": "true"}).json()
    assert len(with_spectrum["spectrum"]) == N


def test_scan_toggle_and_dark(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    assert client.post("/api/scan/stop").json()["scanning"] is False
    assert client.post("/api/scan/start").json()["scanning"] is True
    assert client.post("/api/dark").json()["ok"] is True
    assert client.delete("/api/dark").json()["ok"] is True


def test_status_tracks_runtime_dark(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    assert client.get("/api/status").json()["dark_active"] is False
    client.post("/api/dark")
    assert client.get("/api/status").json()["dark_active"] is True
    client.delete("/api/dark")
    assert client.get("/api/status").json()["dark_active"] is False


def test_live_websocket(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.app.state.app_state.engine.measure_once()
    # websocket_connect ignores the client's base_url and defaults to Host:
    # "testserver" (see starlette.testclient), so a loopback Host must be
    # pinned explicitly for the new Host guard to accept the connection.
    with client.websocket_connect("/api/live", headers={"host": "127.0.0.1"}) as ws:
        body = ws.receive_json()
        assert body["luminance_cdm2"] >= 0
        assert len(body["wavelengths"]) == N
        assert len(body["spectrum"]) == N


def test_status_reports_engine_error(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.app.state.app_state.engine.last_error = "RuntimeError: device unplugged"
    assert client.get("/api/status").json()["error"] == "RuntimeError: device unplugged"
    client.app.state.app_state.engine.last_error = None
    assert client.get("/api/status").json()["error"] is None


def test_hostile_origin_cannot_change_state(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    for method, path in [
        ("post", "/api/scan/stop"),
        ("post", "/api/scan/start"),
        ("post", "/api/dark"),
        ("delete", "/api/dark"),
        ("post", "/api/averaging"),
    ]:
        response = getattr(client, method)(path, headers=HOSTILE_ORIGIN)
        assert response.status_code == 403, path
    assert client.app.state.app_state.engine.scanning is True


def test_local_origin_may_change_state(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    assert client.post("/api/scan/stop", headers=LOCAL_ORIGIN).json()["scanning"] is False


def test_hostile_origin_may_still_read_status(tmp_path: Path) -> None:
    # Reads are already same-origin-protected by CORS; only unsafe methods and
    # the WebSocket need the guard.
    assert make_client(tmp_path).get("/api/status", headers=HOSTILE_ORIGIN).status_code == 200


def test_hostile_origin_cannot_open_live_websocket(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.app.state.app_state.engine.measure_once()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect(
            "/api/live", headers={"host": "127.0.0.1", **HOSTILE_ORIGIN}
        ) as ws:
            ws.receive_json()


def test_spoofed_host_rejected_even_for_get(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    response = client.get("/api/status", headers={"host": "attacker.com"})
    assert response.status_code == 403


def test_lan_origin_rejected_when_remote_access_off(tmp_path: Path) -> None:
    client = make_client(tmp_path, remote_access=False)
    response = client.post("/api/scan/stop", headers=LAN_ORIGIN)
    assert response.status_code == 403


def test_lan_origin_allowed_when_remote_access_on(tmp_path: Path) -> None:
    client = make_client(tmp_path, remote_access=True)
    assert client.post("/api/scan/stop", headers=LAN_ORIGIN).json()["scanning"] is False


def test_dns_name_origin_rejected_even_with_remote_access(tmp_path: Path) -> None:
    client = make_client(tmp_path, remote_access=True)
    response = client.post("/api/scan/stop", headers={"origin": "http://pca.local:5175"})
    assert response.status_code == 403


def test_spoofed_host_rejected_for_websocket(tmp_path: Path) -> None:
    client = make_client(tmp_path)
    client.app.state.app_state.engine.measure_once()
    with pytest.raises(WebSocketDisconnect):
        with client.websocket_connect("/api/live", headers={"host": "attacker.com"}) as ws:
            ws.receive_json()


def test_build_app_starts_without_calibration(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    from pca import main

    monkeypatch.setattr("pca.main.calibration_present", lambda: False)
    monkeypatch.setattr("pca.main.calibration_dir", lambda: tmp_path)
    app = main.build_app()
    with _client(app) as client:
        assert client.get("/api/status").json()["calibration_present"] is False
