"""POST /api/history/export: write the measurement history as CSV and reveal it in Finder."""
import csv
import subprocess
from datetime import datetime
from pathlib import Path
from typing import TextIO

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

COLUMNS = [
    "label", "note", "luminance_ftl", "luminance_cdm2", "x", "y",
    "cct_k", "duv", "integration_ms", "stability", "timestamp",
]  # fmt: skip


class HistoryMeasurement(BaseModel):
    luminance_ftl: float
    luminance_cdm2: float
    x: float
    y: float
    cct_k: float
    duv: float
    integration_ms: float
    stability: str
    timestamp: str


class HistoryEntry(BaseModel):
    label: str = ""
    note: str = ""
    measurement: HistoryMeasurement


class ExportResponse(BaseModel):
    path: str


def export_dir() -> Path:
    return Path.home() / "Downloads"


FORMULA_PREFIXES = ("=", "+", "-", "@", "\t", "\r")


def _text(value: str) -> str:
    """Neutralise spreadsheet formula injection in free-text cells."""
    return f"'{value}" if value.startswith(FORMULA_PREFIXES) else value


def _row(entry: HistoryEntry) -> list[str]:
    m = entry.measurement
    return [
        _text(entry.label),
        _text(entry.note),
        f"{m.luminance_ftl:.3f}",
        f"{m.luminance_cdm2:.3f}",
        f"{m.x:.4f}",
        f"{m.y:.4f}",
        f"{m.cct_k:.0f}",
        f"{m.duv:.4f}",
        f"{m.integration_ms:g}",
        _text(m.stability),
        m.timestamp,
    ]


def _open_new(directory: Path) -> tuple[Path, TextIO]:
    """Open a fresh export file; a second export in the same second gets -2, -3, ..."""
    stem = f"PCA-100-history-{datetime.now():%Y-%m-%d-%H%M%S}"
    suffix = 1
    while True:
        path = directory / (f"{stem}.csv" if suffix == 1 else f"{stem}-{suffix}.csv")
        try:
            return path, path.open("x", newline="", encoding="utf-8")
        except FileExistsError:
            suffix += 1


def _write_csv(entries: list[HistoryEntry], directory: Path) -> Path:
    directory.mkdir(parents=True, exist_ok=True)
    path, handle = _open_new(directory)
    with handle:
        writer = csv.writer(handle)
        writer.writerow(COLUMNS)
        writer.writerows(_row(entry) for entry in entries)
    return path


def register_history(app: FastAPI) -> None:
    @app.post("/api/history/export")
    def post_history_export(entries: list[HistoryEntry]) -> ExportResponse:
        if not entries:
            raise HTTPException(status_code=400, detail="History is empty")
        path = _write_csv(entries, export_dir())
        subprocess.run(["open", "-R", str(path)], check=False)
        return ExportResponse(path=str(path))
