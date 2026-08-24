"""Entry point: assemble AppState and run uvicorn."""
import asyncio
import contextlib
import os
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

import pca.settings
import pca.updater as updater
from pca.api import create_app
from pca.calibration import load_unit
from pca.device import open_first_available
from pca.engine import AppState, Engine, run_loop
from pca.resources import (
    calibration_dir,
    calibration_present,
    resource_frontend_dir,
)
from pca.server import ServerSupervisor, uvicorn_factory

LOOPBACK = "127.0.0.1"
# Every interface: only ever selected when the operator opts into remote access.
ALL_INTERFACES = "0.0.0.0"
PORT = int(os.environ.get("PCA_PORT", "8320"))


def resolve_host(remote_access: bool) -> str:
    """Bind address for the dev/CLI entry point; PCA_HOST still wins if set."""
    override = os.environ.get("PCA_HOST")
    if override:
        return override
    return ALL_INTERFACES if remote_access else LOOPBACK


def load_engine() -> Engine | None:
    if not calibration_present():
        return None
    unit = load_unit(calibration_dir())
    # Original app's effective processing matches seabreeze NL correction off
    # (side-by-side calibration 2026-07-24); the INI NLCorrection flag documents
    # the original's intent, not seabreeze behavior.
    return Engine(unit, connect=lambda: open_first_available(nl_correction=False))


async def _check_for_updates(state: AppState) -> None:
    """Populate AppState.update_info in the background; never raise into the caller."""
    with contextlib.suppress(Exception):
        state.update_info = await asyncio.to_thread(updater.check_latest)


def build_app() -> FastAPI:
    state = AppState(
        engine=load_engine(),
        load_engine=load_engine,
        calibration_dir=calibration_dir(),
        remote_access=pca.settings.get_remote_access(),
        port=PORT,
    )
    app = create_app(state, frontend_dir=resource_frontend_dir())

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        task = asyncio.create_task(run_loop(state))
        update_task = asyncio.create_task(_check_for_updates(state))
        try:
            yield
        finally:
            task.cancel()
            update_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task
            with contextlib.suppress(asyncio.CancelledError):
                await update_task

    app.router.lifespan_context = lifespan
    return app


def build_server(app: FastAPI) -> ServerSupervisor:
    """Wire the app to a runtime-rebindable supervisor.

    The toggle routes through `resolve_host`, so an explicit PCA_HOST pins the
    bind: with it set, both toggle states resolve to the same address and the
    rebind is a no-op. Without it, the toggle moves the socket between loopback
    and every interface at runtime, exactly like the packaged app.
    """
    state: AppState = app.state.app_state
    supervisor = ServerSupervisor(
        port=PORT, start=uvicorn_factory(app), host=resolve_host(state.remote_access)
    )
    state.on_remote_access_change = lambda enabled: supervisor.set_host(resolve_host(enabled))
    return supervisor


def main() -> None:
    build_server(build_app()).serve_forever()


if __name__ == "__main__":
    main()
