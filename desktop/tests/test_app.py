import json
import sys
import threading
import time
import urllib.request
from collections.abc import Callable
from pathlib import Path
from types import SimpleNamespace

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import app as desktop_app
from app import (
    ALL_INTERFACES,
    LOOPBACK,
    RunningServer,
    ServerSupervisor,
    build_supervisor,
    find_free_port,
    host_for,
    uvicorn_factory,
    wait_for_health,
)

from pca.engine import AppState

PORT = 45999


class FakeServer:
    """Stands in for uvicorn.Server: a thread that spins until should_exit."""

    def __init__(self, host: str, port: int, die: bool, on_started: Callable[[], None] | None):
        self.host = host
        self.port = port
        self.die = die
        self.started = False
        self.stopped_by: str | None = None
        self._should_exit = False
        self._on_started = on_started

    @property
    def should_exit(self) -> bool:
        return self._should_exit

    @should_exit.setter
    def should_exit(self, value: bool) -> None:
        self._should_exit = value
        if value:
            self.stopped_by = threading.current_thread().name

    def run(self) -> None:
        if self.die:  # a real bind failure exits uvicorn's run()
            return
        self.started = True
        if self._on_started is not None:
            self._on_started()
        while not self._should_exit:
            time.sleep(0.005)


def make_factory(
    on_started: Callable[[], None] | None = None,
    fail_times: int = 0,
    fail_host: str | None = None,
) -> tuple[Callable[[str, int], RunningServer], list[FakeServer]]:
    created: list[FakeServer] = []
    budget = {"fails": fail_times}
    fired = {"started": False}

    def start(host: str, port: int) -> RunningServer:
        die = host == fail_host
        if not die and budget["fails"] > 0:
            budget["fails"] -= 1
            die = True
        hook = None
        if on_started is not None and not fired["started"] and not die:
            fired["started"] = True
            hook = on_started
        server = FakeServer(host, port, die=die, on_started=hook)
        created.append(server)
        thread = threading.Thread(target=server.run, daemon=True, name=f"fake-{host}")
        thread.start()
        return RunningServer(host=host, server=server, thread=thread)

    return start, created


def wait_until(predicate: Callable[[], bool], timeout_s: float = 5.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return False


def test_host_for_maps_the_toggle_to_a_bind_address() -> None:
    assert host_for(False) == LOOPBACK
    assert host_for(True) == ALL_INTERFACES


def test_starts_on_the_initial_host() -> None:
    start, created = make_factory()
    supervisor = ServerSupervisor(port=PORT, start=start, host=LOOPBACK)
    supervisor.start()
    try:
        assert supervisor.host == LOOPBACK
        assert [(s.host, s.port) for s in created] == [(LOOPBACK, PORT)]
    finally:
        supervisor.stop()


def test_set_host_stops_the_old_server_and_rebinds_the_same_port() -> None:
    start, created = make_factory()
    supervisor = ServerSupervisor(port=PORT, start=start, host=LOOPBACK)
    supervisor.start()
    try:
        supervisor.set_host(ALL_INTERFACES)
        assert wait_until(lambda: supervisor.host == ALL_INTERFACES)
        assert len(created) == 2
        assert created[0].should_exit is True
        assert created[1].host == ALL_INTERFACES
        assert created[1].port == PORT
        assert created[1].should_exit is False
    finally:
        supervisor.stop()
    assert created[1].should_exit is True


def test_set_host_to_the_current_host_does_not_restart() -> None:
    start, created = make_factory()
    supervisor = ServerSupervisor(port=PORT, start=start, host=LOOPBACK)
    supervisor.start()
    try:
        supervisor.set_host(LOOPBACK)
        time.sleep(0.2)
        assert len(created) == 1
        assert created[0].should_exit is False
    finally:
        supervisor.stop()


def test_set_host_called_from_the_server_thread_does_not_block_or_deadlock() -> None:
    """The POST handler runs on the server being torn down; it must return at once."""
    elapsed: list[float] = []
    supervisor_box: list[ServerSupervisor] = []

    def toggle_from_request_handler() -> None:
        started = time.monotonic()
        supervisor_box[0].set_host(ALL_INTERFACES)
        elapsed.append(time.monotonic() - started)

    start, created = make_factory(on_started=toggle_from_request_handler)
    supervisor = ServerSupervisor(port=PORT, start=start, host=LOOPBACK)
    supervisor_box.append(supervisor)
    supervisor.start()
    try:
        assert wait_until(lambda: supervisor.host == ALL_INTERFACES)
        assert elapsed and elapsed[0] < 0.5
        assert created[0].stopped_by == "pca-http-supervisor"
    finally:
        supervisor.stop()


def test_bind_retries_when_the_first_attempt_dies() -> None:
    start, created = make_factory(fail_times=1)
    supervisor = ServerSupervisor(port=PORT, start=start, host=LOOPBACK)
    supervisor.start()
    try:
        assert len(created) == 2
        assert created[0].die is True
        assert created[1].started is True
        assert supervisor.host == LOOPBACK
    finally:
        supervisor.stop()


def test_bind_gives_up_after_the_attempt_budget() -> None:
    start, _ = make_factory(fail_times=99)
    supervisor = ServerSupervisor(port=PORT, start=start, host=LOOPBACK)
    with pytest.raises(RuntimeError, match="could not bind"):
        supervisor.start()


def test_a_refused_rebind_falls_back_to_the_address_that_worked() -> None:
    start, created = make_factory(fail_host=ALL_INTERFACES)
    supervisor = ServerSupervisor(port=PORT, start=start, host=LOOPBACK)
    supervisor.start()
    try:
        supervisor.set_host(ALL_INTERFACES)
        assert wait_until(lambda: supervisor.last_error is not None)
        assert wait_until(lambda: created[-1].started and created[-1].host == LOOPBACK)
        assert supervisor.host == LOOPBACK
        assert supervisor.last_error == f"could not bind {ALL_INTERFACES}:{PORT}"
        time.sleep(0.2)  # the dropped wish must not be retried in a loop
        assert created[-1].should_exit is False
    finally:
        supervisor.stop()


def test_build_supervisor_wires_state_port_host_and_toggle_callback(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = AppState(
        engine=None, load_engine=lambda: None, calibration_dir=tmp_path, remote_access=True
    )
    fake_app = SimpleNamespace(state=SimpleNamespace(app_state=state))
    monkeypatch.setattr(desktop_app, "build_app", lambda: fake_app)
    supervisor = build_supervisor(PORT)

    assert state.port == PORT
    assert supervisor.port == PORT
    assert supervisor.host == ALL_INTERFACES
    assert state.on_remote_access_change is not None
    state.on_remote_access_change(False)
    assert supervisor.host == LOOPBACK


def test_health_after_server_start_and_after_a_rebind_of_the_same_app() -> None:
    """Real sockets from here down - loopback only, a test never opens the LAN."""
    from pca.main import build_app

    app = build_app()
    port = find_free_port()
    start = uvicorn_factory(app)
    for _ in range(2):
        running = start(LOOPBACK, port)
        try:
            assert wait_for_health(port, timeout_s=60.0) is True
        finally:
            running.server.should_exit = True
            running.thread.join(timeout=30.0)
        assert running.thread.is_alive() is False


def loopback_only_factory(app: object) -> Callable[[str, int], RunningServer]:
    """Real uvicorn, but every requested address lands on loopback."""
    real = uvicorn_factory(app)  # type: ignore[arg-type]

    def start(host: str, port: int) -> RunningServer:
        running = real(LOOPBACK, port)
        return RunningServer(host=host, server=running.server, thread=running.thread)

    return start


def post_remote_access(port: int, enabled: bool) -> dict[str, object]:
    request = urllib.request.Request(
        f"http://{LOOPBACK}:{port}/api/remote-access",
        data=json.dumps({"enabled": enabled}).encode(),
        headers={"content-type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=30.0) as response:
        body: dict[str, object] = json.load(response)
    return body


def test_toggling_remote_access_over_http_rebinds_without_deadlocking(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The toggle handler runs on the server it is about to stop."""
    import pca.settings

    monkeypatch.setattr(pca.settings, "_SETTINGS_PATH", tmp_path / "settings.json")
    monkeypatch.setattr("pca.main.calibration_present", lambda: False)
    monkeypatch.setattr("pca.main.calibration_dir", lambda: tmp_path)
    monkeypatch.setattr(desktop_app, "uvicorn_factory", loopback_only_factory)

    port = find_free_port()
    supervisor = build_supervisor(port)
    supervisor.start()
    try:
        assert supervisor.host == LOOPBACK
        assert wait_for_health(port, timeout_s=60.0) is True
        assert post_remote_access(port, True)["enabled"] is True
        assert wait_until(lambda: supervisor.host == ALL_INTERFACES, timeout_s=60.0)
        # the webview never moves off loopback, and the new bind still serves it
        assert wait_for_health(port, timeout_s=60.0) is True
        assert post_remote_access(port, False)["enabled"] is False
        assert wait_until(lambda: supervisor.host == LOOPBACK, timeout_s=60.0)
        assert wait_for_health(port, timeout_s=60.0) is True
    finally:
        supervisor.stop()


def test_a_rebind_does_not_reopen_the_spectrometer(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import numpy as np

    from pca.device import FakeSpectrometer
    from pca.engine import Engine
    from tests.test_engine import make_unit

    wavelengths = np.linspace(380.0, 780.0, 32)
    device = FakeSpectrometer(wavelengths, [np.full(32, 30_000.0)])
    opens: list[object] = []

    def connect() -> FakeSpectrometer:
        opens.append(device)
        return device

    engine = Engine(make_unit(wavelengths), connect=connect)
    monkeypatch.setattr("pca.main.load_engine", lambda: engine)
    monkeypatch.setattr("pca.main.calibration_dir", lambda: tmp_path)
    monkeypatch.setattr(desktop_app, "uvicorn_factory", loopback_only_factory)

    port = find_free_port()
    supervisor = build_supervisor(port)
    supervisor.start()
    try:
        assert wait_for_health(port, timeout_s=60.0) is True
        assert wait_until(lambda: engine.connected, timeout_s=60.0)
        reads = len(device.read_log)
        supervisor.set_host(ALL_INTERFACES)
        assert wait_until(lambda: supervisor.host == ALL_INTERFACES, timeout_s=60.0)
        assert wait_for_health(port, timeout_s=60.0) is True
        assert wait_until(lambda: len(device.read_log) > reads, timeout_s=60.0)
        assert opens == [device]  # the USB device outlived the socket swap
        assert engine.connected is True
    finally:
        supervisor.stop()


def test_run_persists_web_storage(monkeypatch: pytest.MonkeyPatch) -> None:
    """History lives in webview localStorage; private mode would wipe it on quit."""
    calls: dict[str, object] = {}

    class _StubSupervisor:
        def start(self) -> None:
            return None

        def stop(self) -> None:
            return None

    class _StubWebview:
        def create_window(self, *args: object, **kwargs: object) -> None:
            calls["window"] = kwargs

        def start(self, **kwargs: object) -> None:
            calls["start"] = kwargs

    monkeypatch.setattr(desktop_app, "find_free_port", lambda: 12345)
    monkeypatch.setattr(desktop_app, "build_supervisor", lambda port: _StubSupervisor())
    monkeypatch.setattr(desktop_app, "wait_for_health", lambda port, timeout_s: True)
    monkeypatch.setattr(desktop_app, "webview", _StubWebview())

    desktop_app.run()

    assert calls["window"]["text_select"] is True
    start_kwargs = calls["start"]
    assert start_kwargs["private_mode"] is False
    assert "PCA-100" in str(start_kwargs["storage_path"])
