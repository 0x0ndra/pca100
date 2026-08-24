"""REST + WebSocket API exposing the measurement engine."""
import asyncio
import contextlib
import subprocess
from collections.abc import Awaitable, Callable
from pathlib import Path

import segno
from fastapi import FastAPI, HTTPException, Request, Response, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import pca
import pca.settings
from pca import netguard
from pca.api_history import register_history
from pca.api_update import register_update
from pca.engine import AppState, Engine, Measurement
from pca.netguard import UNSAFE_METHODS, is_allowed_host, is_allowed_origin

WS_POLL_INTERVAL_S = 0.1
WS_POLICY_VIOLATION = 1008


class StatusResponse(BaseModel):
    connected: bool
    serial: str
    scanning: bool
    averaging: bool
    integration_ms: float
    dark_active: bool
    calibration_present: bool
    version: str
    error: str | None = None


class AveragingRequest(BaseModel):
    enabled: bool


class RemoteAccessRequest(BaseModel):
    enabled: bool


class RemoteAccessResponse(BaseModel):
    enabled: bool
    urls: list[str]
    qr: str | None = None


class MeasurementResponse(BaseModel):
    luminance_ftl: float
    luminance_cdm2: float
    x: float
    y: float
    cct_k: float
    duv: float
    integration_ms: float
    stable: bool
    stability: str
    variation_pct: float
    saturated: bool
    timestamp: str
    wavelengths: list[float] | None = None
    spectrum: list[float] | None = None

    @classmethod
    def from_measurement(cls, m: Measurement, include_spectrum: bool) -> "MeasurementResponse":
        return cls(
            luminance_ftl=m.reading.luminance_ftl,
            luminance_cdm2=m.reading.luminance_cdm2,
            x=m.reading.x,
            y=m.reading.y,
            cct_k=m.reading.cct_k,
            duv=m.reading.duv,
            integration_ms=m.integration_us / 1000,
            stable=m.stable,
            stability=m.stability,
            variation_pct=m.variation_pct,
            saturated=m.saturated,
            timestamp=m.timestamp.isoformat(),
            wavelengths=m.wavelengths.tolist() if include_spectrum else None,
            spectrum=m.spectrum.tolist() if include_spectrum else None,
        )


def _status(state: AppState) -> StatusResponse:
    engine = state.engine
    if engine is None:
        return StatusResponse(
            connected=False, serial="", scanning=False, averaging=False,
            integration_ms=0.0, dark_active=False, calibration_present=False,
            version=pca.__version__, error=None,
        )
    return StatusResponse(
        connected=engine.connected, serial=engine.serial, scanning=engine.scanning,
        averaging=engine.averaging, integration_ms=engine.integration_us / 1000,
        dark_active=engine.dark_active, calibration_present=True,
        version=pca.__version__, error=engine.last_error,
    )


def _require_engine(state: AppState) -> Engine:
    if state.engine is None:
        raise HTTPException(status_code=409, detail="no calibration loaded")
    return state.engine


def _register_status_and_measurement(app: FastAPI, state: AppState) -> None:
    @app.get("/api/status")
    def get_status() -> StatusResponse:
        return _status(state)

    @app.get("/api/measurement", response_model_exclude_none=True)
    def get_measurement(spectrum: bool = False) -> MeasurementResponse:
        engine = _require_engine(state)
        if engine.latest is None:
            raise HTTPException(status_code=404, detail="no measurement yet")
        return MeasurementResponse.from_measurement(engine.latest, spectrum)


def _register_scan(app: FastAPI, state: AppState) -> None:
    @app.post("/api/scan/start")
    def scan_start() -> StatusResponse:
        _require_engine(state).start()
        return _status(state)

    @app.post("/api/scan/stop")
    def scan_stop() -> StatusResponse:
        _require_engine(state).stop()
        return _status(state)


def _register_averaging(app: FastAPI, state: AppState) -> None:
    @app.post("/api/averaging")
    def set_averaging(body: AveragingRequest) -> StatusResponse:
        _require_engine(state).set_averaging(body.enabled)
        return _status(state)


def _register_dark(app: FastAPI, state: AppState) -> None:
    @app.post("/api/dark")
    def dark_capture() -> dict[str, bool]:
        _require_engine(state).capture_dark()
        return {"ok": True}

    @app.delete("/api/dark")
    def dark_clear() -> dict[str, bool]:
        _require_engine(state).clear_dark()
        return {"ok": True}


def _register_calibration(app: FastAPI, state: AppState) -> None:
    @app.post("/api/calibration/reload")
    def reload_calibration() -> dict[str, bool]:
        old_engine = state.engine
        state.engine = state.load_engine()
        if old_engine is not None:
            old_engine.close()
        return {"calibration_present": state.engine is not None}

    @app.post("/api/calibration/reveal")
    def reveal_calibration() -> dict[str, bool]:
        subprocess.run(["open", str(state.calibration_dir)], check=False)
        return {"ok": True}


def _qr_data_uri(url: str) -> str:
    return segno.make(url).png_data_uri(scale=4, border=2)


def _remote_access_response(state: AppState) -> RemoteAccessResponse:
    if not state.remote_access:
        return RemoteAccessResponse(enabled=False, urls=[], qr=None)
    ips = netguard.ranked_connect_ips(netguard.local_ipv4s())
    urls = [f"http://{ip}:{state.port}" for ip in ips]
    qr = _qr_data_uri(urls[0]) if urls else None
    return RemoteAccessResponse(enabled=True, urls=urls, qr=qr)


def _register_remote_access(app: FastAPI, state: AppState) -> None:
    @app.get("/api/remote-access")
    def get_remote_access() -> RemoteAccessResponse:
        return _remote_access_response(state)

    @app.post("/api/remote-access")
    def set_remote_access(body: RemoteAccessRequest) -> RemoteAccessResponse:
        pca.settings.set_remote_access(body.enabled)
        state.remote_access = body.enabled
        if state.on_remote_access_change is not None:
            state.on_remote_access_change(body.enabled)
        return _remote_access_response(state)


async def _poll_and_send(websocket: WebSocket, state: AppState) -> None:
    last: Measurement | None = None
    while True:
        engine = state.engine
        if engine is None:
            await asyncio.sleep(WS_POLL_INTERVAL_S)
            continue
        current = engine.latest
        if current is not None and current is not last:
            last = current
            response = MeasurementResponse.from_measurement(current, True)
            await websocket.send_json(response.model_dump(exclude_none=True))
        await asyncio.sleep(WS_POLL_INTERVAL_S)


def _register_origin_guard(app: FastAPI, state: AppState) -> None:
    lan = netguard.local_ipv4s()

    @app.middleware("http")
    async def guard_origin(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if not is_allowed_host(
            request.headers.get("host"), state.remote_access, state.port, lan
        ):
            return JSONResponse({"detail": "host not allowed"}, status_code=403)
        if request.method in UNSAFE_METHODS and not is_allowed_origin(
            request.headers.get("origin"), state.remote_access, lan
        ):
            return JSONResponse({"detail": "origin not allowed"}, status_code=403)
        return await call_next(request)


def _register_live(app: FastAPI, state: AppState) -> None:
    lan = netguard.local_ipv4s()

    @app.websocket("/api/live")
    async def live(websocket: WebSocket) -> None:
        if not is_allowed_host(
            websocket.headers.get("host"), state.remote_access, state.port, lan
        ):
            await websocket.close(code=WS_POLICY_VIOLATION)
            return
        if not is_allowed_origin(websocket.headers.get("origin"), state.remote_access, lan):
            await websocket.close(code=WS_POLICY_VIOLATION)
            return
        await websocket.accept()
        poll_task = asyncio.create_task(_poll_and_send(websocket, state))
        try:
            while True:
                message = await websocket.receive()
                if message["type"] == "websocket.disconnect":
                    break
        except WebSocketDisconnect:
            pass
        finally:
            poll_task.cancel()
            with contextlib.suppress(asyncio.CancelledError, WebSocketDisconnect):
                await poll_task


def create_app(state: AppState, frontend_dir: Path | None = None) -> FastAPI:
    app = FastAPI()
    app.state.app_state = state
    _register_origin_guard(app, state)
    _register_status_and_measurement(app, state)
    _register_scan(app, state)
    _register_averaging(app, state)
    _register_dark(app, state)
    _register_calibration(app, state)
    _register_remote_access(app, state)
    register_update(app, state)
    register_history(app)
    _register_live(app, state)
    if frontend_dir is not None and frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")
    return app
