"""GET/POST /api/update endpoints: cached GitHub release check + DMG download."""
import asyncio
import subprocess

from fastapi import FastAPI
from pydantic import BaseModel

import pca
import pca.updater as updater
from pca.engine import AppState, DownloadState


class DownloadStateResponse(BaseModel):
    state: str
    error: str | None = None
    path: str | None = None


class UpdateResponse(BaseModel):
    current: str
    latest: str | None = None
    available: bool = False
    release_url: str | None = None
    error: str | None = None
    download: DownloadStateResponse


def _update_response(state: AppState) -> UpdateResponse:
    info = state.update_info or updater.UpdateInfo(current=pca.__version__)
    download = state.download
    return UpdateResponse(
        current=info.current,
        latest=info.latest,
        available=info.available,
        release_url=info.release_url,
        error=info.error,
        download=DownloadStateResponse(
            state=download.state,
            error=download.error,
            path=str(download.path) if download.path else None,
        ),
    )


def register_update(app: FastAPI, state: AppState) -> None:
    @app.get("/api/update")
    def get_update() -> UpdateResponse:
        return _update_response(state)

    @app.post("/api/update/download")
    async def post_update_download() -> UpdateResponse:
        if state.download.state == "downloading":
            return _update_response(state)
        asset_url = state.update_info.asset_url if state.update_info else None
        if not asset_url:
            return _update_response(state)
        state.download = DownloadState(state="downloading")
        try:
            path = await asyncio.to_thread(updater.download_dmg, asset_url)
        except Exception as exc:
            state.download = DownloadState(state="error", error=f"{type(exc).__name__}: {exc}")
            return _update_response(state)
        await asyncio.to_thread(subprocess.run, ["open", str(path)], check=False)
        state.download = DownloadState(state="downloaded", path=path)
        return _update_response(state)
