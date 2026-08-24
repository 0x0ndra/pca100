"""Native macOS shell: run the API in a thread and show it in a WKWebView.

The HTTP socket is owned by `ServerSupervisor` (in `pca.server`), which rebinds
it at runtime (loopback <-> every interface) when the operator toggles remote
access. Only the socket is recycled: the FastAPI app, the AppState, the
measurement loop's engine and its USB connection to the spectrometer all
outlive a rebind.
"""
import socket
import sys
import time
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

import webview

from pca.engine import AppState
from pca.main import ALL_INTERFACES, LOOPBACK, build_app
from pca.server import (
    RunningServer,
    ServerFactory,
    ServerSupervisor,
    StoppableServer,
    uvicorn_factory,
)

__all__ = [
    "RunningServer",
    "ServerFactory",
    "ServerSupervisor",
    "StoppableServer",
    "ALL_INTERFACES",
    "LOOPBACK",
    "build_app",
    "build_supervisor",
    "find_free_port",
    "host_for",
    "run",
    "uvicorn_factory",
    "wait_for_health",
]

WINDOW_TITLE = "PCA-100"


def find_free_port() -> int:
    # Probed on every interface, not just loopback: the same port has to be
    # free once more when remote access rebinds the socket to 0.0.0.0.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("", 0))
        return int(s.getsockname()[1])


def wait_for_health(port: int, timeout_s: float) -> bool:
    deadline = time.monotonic() + timeout_s
    url = f"http://{LOOPBACK}:{port}/api/status"
    while time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1.0) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.2)
    return False


def host_for(remote_access: bool) -> str:
    return ALL_INTERFACES if remote_access else LOOPBACK


def build_supervisor(port: int) -> ServerSupervisor:
    """One app, one AppState, one engine - a rebind recycles the socket only."""
    app = build_app()
    state: AppState = app.state.app_state
    state.port = port
    supervisor = ServerSupervisor(
        port=port, start=uvicorn_factory(app), host=host_for(state.remote_access)
    )
    state.on_remote_access_change = lambda enabled: supervisor.set_host(host_for(enabled))
    return supervisor


def run() -> None:
    port = find_free_port()
    supervisor = build_supervisor(port)
    supervisor.start()
    if not wait_for_health(port, timeout_s=30.0):
        print(f"error: backend did not become healthy on port {port} within 30s", file=sys.stderr)
        raise SystemExit(1)
    # Measurement history lives in the webview's localStorage; pywebview's
    # default private mode would silently wipe it on every quit.
    storage = Path.home() / "Library" / "Application Support" / "PCA-100" / "webview"
    storage.mkdir(parents=True, exist_ok=True)
    webview.create_window(
        WINDOW_TITLE,
        f"http://{LOOPBACK}:{port}/",
        width=1280,
        height=900,
        text_select=True,
    )
    webview.start(private_mode=False, storage_path=str(storage))
    supervisor.stop()


if __name__ == "__main__":
    run()
