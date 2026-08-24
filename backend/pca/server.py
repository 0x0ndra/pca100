"""Runtime-rebindable HTTP server, shared by both entry points.

`ServerSupervisor` owns the current uvicorn socket and swaps it (loopback <->
every interface) off the request path when the operator toggles remote access.
Only the socket is recycled: the FastAPI app, its AppState, the measurement
loop's engine and its USB connection all outlive a rebind.

This is a leaf module: it depends on uvicorn + stdlib only, never on lower pca
layers, so it stays importable from both `desktop/app.py` (which drives pywebview
on the main thread) and `pca.main` (the dev/CLI entry point).
"""
import signal
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from types import FrameType
from typing import Any, Protocol

import uvicorn
from fastapi import FastAPI

LOOPBACK = "127.0.0.1"

STOP_TIMEOUT_S = 10.0
START_TIMEOUT_S = 5.0
BIND_ATTEMPTS = 3
BIND_RETRY_S = 0.25
POLL_S = 0.02
IDLE_POLL_S = 0.2


class StoppableServer(Protocol):
    """The slice of `uvicorn.Server` the supervisor drives."""

    started: bool
    should_exit: bool


@dataclass
class RunningServer:
    host: str
    server: StoppableServer
    thread: threading.Thread


ServerFactory = Callable[[str, int], RunningServer]


def uvicorn_factory(app: FastAPI) -> ServerFactory:
    def start(host: str, port: int) -> RunningServer:
        config = uvicorn.Config(app, host=host, port=port, log_level="warning")
        server = uvicorn.Server(config)
        thread = threading.Thread(target=server.run, daemon=True, name=f"pca-http-{host}")
        thread.start()
        return RunningServer(host=host, server=server, thread=thread)

    return start


def _stop(running: RunningServer) -> None:
    running.server.should_exit = True
    running.thread.join(timeout=STOP_TIMEOUT_S)


def _await_start(running: RunningServer) -> bool:
    """True once the server reports itself started, False if its thread died first."""
    deadline = time.monotonic() + START_TIMEOUT_S
    while time.monotonic() < deadline:
        if running.server.started:
            return True
        if not running.thread.is_alive():
            return False
        time.sleep(POLL_S)
    return running.thread.is_alive()


class ServerSupervisor:
    """Owns the current HTTP server and rebinds it off the request path.

    `set_host` records the wish and wakes a dedicated worker thread instead of
    swapping inline: its caller is a request handler of the very server about
    to be torn down, so stopping and joining there would deadlock.
    """

    def __init__(self, port: int, start: ServerFactory, host: str = LOOPBACK) -> None:
        self._port = port
        self._start = start
        self._lock = threading.Lock()
        self._current: RunningServer | None = None
        self._desired_host = host
        self._wake = threading.Event()
        self._shutdown = False
        self._worker: threading.Thread | None = None
        self.last_error: str | None = None

    @property
    def port(self) -> int:
        return self._port

    @property
    def host(self) -> str:
        """The address currently bound, not a pending wish."""
        with self._lock:
            return self._current.host if self._current is not None else self._desired_host

    def start(self) -> None:
        with self._lock:
            if self._current is not None:
                return
            host = self._desired_host
        running = self._bind(host)
        if running is None:
            raise RuntimeError(f"could not bind {host}:{self._port}")
        with self._lock:
            self._current = running
        self._worker = threading.Thread(
            target=self._serve_wishes, daemon=True, name="pca-http-supervisor"
        )
        self._worker.start()

    def serve_forever(self) -> None:
        """Start the server and block until stopped (Ctrl+C or SIGTERM) - the CLI entry point.

        Uvicorn always runs on a background thread here (see `uvicorn_factory`),
        so its own SIGTERM handling never installs; a bare `kill <pid>` would
        otherwise terminate the process with no graceful shutdown. Installing a
        handler that raises KeyboardInterrupt routes SIGTERM through the exact
        same, already-tested shutdown path as Ctrl+C.
        """
        previous_sigterm = self._install_sigterm_handler()
        self.start()
        try:
            while not self._shutdown:
                time.sleep(IDLE_POLL_S)
        except KeyboardInterrupt:
            pass
        finally:
            self.stop()
            signal.signal(signal.SIGTERM, previous_sigterm)

    def _install_sigterm_handler(self) -> Any:
        """Register a SIGTERM handler and return the previous one.

        Only valid on the main thread (a `signal.signal` requirement), which is
        where `serve_forever` runs. Split out so a test can register, invoke,
        and restore the handler without sending a real signal or a subprocess.
        """

        def _on_sigterm(signum: int, frame: FrameType | None) -> None:
            raise KeyboardInterrupt

        return signal.signal(signal.SIGTERM, _on_sigterm)

    def set_host(self, host: str) -> None:
        """Ask for a rebind and return at once; the swap runs on the worker."""
        with self._lock:
            self._desired_host = host
        self._wake.set()

    def stop(self) -> None:
        with self._lock:
            if self._shutdown:
                return
            self._shutdown = True
            running, self._current = self._current, None
        self._wake.set()
        if running is not None:
            _stop(running)
        if self._worker is not None:
            self._worker.join(timeout=STOP_TIMEOUT_S)
            self._worker = None

    def _serve_wishes(self) -> None:
        while True:
            self._wake.wait()
            self._wake.clear()
            with self._lock:
                if self._shutdown:
                    return
            self._reconcile()

    def _reconcile(self) -> None:
        while True:
            with self._lock:
                if self._shutdown:
                    return
                running, desired = self._current, self._desired_host
            if running is None or running.host == desired:
                return
            _stop(running)
            if not self._swap(desired, running.host):
                return

    def _swap(self, desired: str, previous: str) -> bool:
        """Rebind to `desired`, falling back to `previous` if it will not take.

        A refused bind must not cost the operator their running app, so the
        socket goes back where it was and the wish is dropped rather than
        retried forever; the toggle simply does not take effect.
        """
        replacement = self._bind(desired)
        if replacement is not None:
            self.last_error = None
        else:
            self.last_error = f"could not bind {desired}:{self._port}"
            replacement = self._bind(previous)
        landed = replacement.host if replacement is not None else previous
        with self._lock:
            if self._shutdown:
                orphan, self._current = replacement, None
            else:
                orphan, self._current = None, replacement
                if landed != desired and self._desired_host == desired:
                    self._desired_host = landed  # drop a wish that will not bind
        if orphan is not None:
            _stop(orphan)
            return False
        return landed == desired

    def _bind(self, host: str) -> RunningServer | None:
        """Start a server on `host`, retrying while the old socket lets go."""
        for attempt in range(BIND_ATTEMPTS):
            running = self._start(host, self._port)
            if _await_start(running):
                return running
            if attempt + 1 < BIND_ATTEMPTS:
                time.sleep(BIND_RETRY_S)
        return None
