import threading
import time
from collections.abc import Callable
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from pca import main
from pca.engine import AppState
from pca.server import RunningServer
from pca.updater import UpdateInfo


def _no_calibration(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("pca.main.calibration_present", lambda: False)
    monkeypatch.setattr("pca.main.calibration_dir", lambda: tmp_path)


class _FakeServer:
    """A uvicorn.Server stand-in: a thread that spins until should_exit, no socket."""

    def __init__(self, host: str) -> None:
        self.host = host
        self.started = False
        self.should_exit = False

    def run(self) -> None:
        self.started = True
        while not self.should_exit:
            time.sleep(0.005)


def _fake_factory(_app: object) -> Callable[[str, int], RunningServer]:
    def start(host: str, port: int) -> RunningServer:
        server = _FakeServer(host)
        thread = threading.Thread(target=server.run, daemon=True, name=f"fake-{host}")
        thread.start()
        return RunningServer(host=host, server=server, thread=thread)

    return start


def _wait_until(predicate: Callable[[], bool], timeout_s: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_dev_entry_point_rebinds_the_socket_when_remote_access_toggles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The bug: `main()` bound the host once and never rebound. build_server wires it."""
    _no_calibration(tmp_path, monkeypatch)
    monkeypatch.delenv("PCA_HOST", raising=False)
    monkeypatch.setattr("pca.settings.get_remote_access", lambda: False)
    monkeypatch.setattr(main, "uvicorn_factory", _fake_factory)

    app = main.build_app()
    state: AppState = app.state.app_state
    supervisor = main.build_server(app)
    supervisor.start()
    try:
        assert supervisor.host == main.LOOPBACK
        assert state.on_remote_access_change is not None
        state.on_remote_access_change(True)
        assert _wait_until(lambda: supervisor.host == main.ALL_INTERFACES)
        state.on_remote_access_change(False)
        assert _wait_until(lambda: supervisor.host == main.LOOPBACK)
    finally:
        supervisor.stop()


def test_pca_host_override_pins_the_bind_across_toggles(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_calibration(tmp_path, monkeypatch)
    monkeypatch.setenv("PCA_HOST", "10.0.0.5")
    monkeypatch.setattr("pca.settings.get_remote_access", lambda: False)
    monkeypatch.setattr(main, "uvicorn_factory", _fake_factory)

    app = main.build_app()
    state: AppState = app.state.app_state
    supervisor = main.build_server(app)
    supervisor.start()
    try:
        assert supervisor.host == "10.0.0.5"
        state.on_remote_access_change(True)
        time.sleep(0.2)
        assert supervisor.host == "10.0.0.5"  # PCA_HOST pins the bind: toggle is a no-op
    finally:
        supervisor.stop()


def test_build_app_seeds_remote_access_from_settings(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_calibration(tmp_path, monkeypatch)
    monkeypatch.setattr("pca.settings.get_remote_access", lambda: True)
    state = main.build_app().state.app_state
    assert state.remote_access is True
    assert state.port == main.PORT


def test_build_app_defaults_to_remote_access_off(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_calibration(tmp_path, monkeypatch)
    monkeypatch.setattr("pca.settings.get_remote_access", lambda: False)
    assert main.build_app().state.app_state.remote_access is False


def test_resolve_host_binds_loopback_unless_remote_access_is_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv("PCA_HOST", raising=False)
    assert main.resolve_host(False) == main.LOOPBACK
    assert main.resolve_host(True) == main.ALL_INTERFACES


def test_resolve_host_honours_the_pca_host_override(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PCA_HOST", "10.0.0.5")
    assert main.resolve_host(False) == "10.0.0.5"
    assert main.resolve_host(True) == "10.0.0.5"


async def test_check_for_updates_populates_state(monkeypatch: pytest.MonkeyPatch) -> None:
    info = UpdateInfo(current="1.1.0", latest="1.2.0", available=True)
    monkeypatch.setattr(main.updater, "check_latest", lambda timeout=5.0: info)
    state = AppState(engine=None, load_engine=lambda: None, calibration_dir=Path("."))
    await main._check_for_updates(state)
    assert state.update_info is info


def test_build_app_lifespan_populates_update_info(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_calibration(tmp_path, monkeypatch)
    monkeypatch.setattr(
        main.updater,
        "check_latest",
        lambda timeout=5.0: UpdateInfo(current="1.1.0", latest="1.2.0", available=True),
    )
    app = main.build_app()
    with TestClient(app, base_url="http://127.0.0.1") as client:
        state: AppState = client.app.state.app_state
        for _ in range(50):
            if state.update_info is not None:
                break
            time.sleep(0.01)
        body = client.get("/api/update").json()
    assert body["latest"] == "1.2.0"
    assert body["available"] is True


def test_build_app_starts_without_blocking_when_update_check_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _no_calibration(tmp_path, monkeypatch)

    def _raise(timeout: float = 5.0) -> UpdateInfo:
        raise RuntimeError("simulated update-check failure")

    monkeypatch.setattr(main.updater, "check_latest", _raise)
    app = main.build_app()
    with TestClient(app, base_url="http://127.0.0.1") as client:
        assert client.get("/api/status").status_code == 200
