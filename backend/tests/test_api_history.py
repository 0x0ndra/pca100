import csv
import re
from datetime import datetime
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from tests.test_api import HOSTILE_ORIGIN, make_client


def entry(label: str = "Left", note: str = "") -> dict:
    return {
        "id": "abc",
        "label": label,
        "note": note,
        "measurement": {
            "luminance_ftl": 14.123456,
            "luminance_cdm2": 48.39876,
            "x": 0.312734,
            "y": 0.329123,
            "cct_k": 6503.6,
            "duv": 0.00123456,
            "integration_ms": 12.5,
            "stable": True,
            "stability": "stable",
            "variation_pct": 0.1,
            "saturated": False,
            "timestamp": "2026-09-30T10:00:00+00:00",
            "wavelengths": [380.0],
            "spectrum": [1.0],
        },
    }


@pytest.fixture
def export_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> tuple[TestClient, Path]:
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    monkeypatch.setattr("pca.api_history.export_dir", lambda: out_dir)
    calls: list[list[str]] = []
    monkeypatch.setattr("pca.api_history.subprocess.run", lambda args, **kw: calls.append(args))
    client = make_client(tmp_path)
    client.reveal_calls = calls  # type: ignore[attr-defined]
    return client, out_dir


def test_export_writes_csv_with_rounding_and_reveals(
    export_client: tuple[TestClient, Path],
) -> None:
    client, out_dir = export_client
    response = client.post("/api/history/export", json=[entry("Left", "a, \"b\"")])
    assert response.status_code == 200
    path = Path(response.json()["path"])
    assert path.parent == out_dir
    assert re.fullmatch(r"PCA-100-history-\d{4}-\d{2}-\d{2}-\d{6}\.csv", path.name)
    rows = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))
    assert rows[0] == [
        "label", "note", "luminance_ftl", "luminance_cdm2", "x", "y",
        "cct_k", "duv", "integration_ms", "stability", "timestamp",
    ]  # fmt: skip
    assert rows[1] == [
        "Left", 'a, "b"', "14.123", "48.399", "0.3127", "0.3291",
        "6504", "0.0012", "12.5", "stable", "2026-09-30T10:00:00+00:00",
    ]  # fmt: skip
    assert client.reveal_calls == [["open", "-R", str(path)]]  # type: ignore[attr-defined]


def test_export_empty_list_is_400(export_client: tuple[TestClient, Path]) -> None:
    client, out_dir = export_client
    assert client.post("/api/history/export", json=[]).status_code == 400
    assert list(out_dir.iterdir()) == []


def test_export_rejects_hostile_origin(export_client: tuple[TestClient, Path]) -> None:
    client, out_dir = export_client
    response = client.post("/api/history/export", json=[entry()], headers=HOSTILE_ORIGIN)
    assert response.status_code == 403
    assert list(out_dir.iterdir()) == []


class FrozenDatetime(datetime):
    @classmethod
    def now(cls, tz: object = None) -> "FrozenDatetime":  # type: ignore[override]
        return cls(2026, 9, 30, 10, 0, 0)


def test_same_second_exports_do_not_overwrite(
    export_client: tuple[TestClient, Path], monkeypatch: pytest.MonkeyPatch
) -> None:
    client, out_dir = export_client
    monkeypatch.setattr("pca.api_history.datetime", FrozenDatetime)
    names = [
        Path(client.post("/api/history/export", json=[entry(label)]).json()["path"]).name
        for label in ("A", "B", "C")
    ]
    stem = "PCA-100-history-2026-09-30-100000"
    assert names == [f"{stem}.csv", f"{stem}-2.csv", f"{stem}-3.csv"]
    labels = [(out_dir / name).read_text(encoding="utf-8").splitlines()[1][0] for name in names]
    assert labels == ["A", "B", "C"]


@pytest.mark.parametrize("prefix", ["=", "+", "-", "@", "\t", "\r"])
def test_export_neutralises_formula_injection(
    export_client: tuple[TestClient, Path], prefix: str
) -> None:
    client, _ = export_client
    payload = entry(f"{prefix}SUM(A1)", f"{prefix}cmd")
    payload["measurement"]["stability"] = f"{prefix}x"
    path = Path(client.post("/api/history/export", json=[payload]).json()["path"])
    with path.open(newline="", encoding="utf-8") as handle:
        row = list(csv.reader(handle))[1]
    assert row[0] == f"'{prefix}SUM(A1)"
    assert row[1] == f"'{prefix}cmd"
    assert row[9] == f"'{prefix}x"


def test_export_keeps_negative_numbers_unquoted(export_client: tuple[TestClient, Path]) -> None:
    client, _ = export_client
    payload = entry()
    payload["measurement"]["duv"] = -0.0021
    path = Path(client.post("/api/history/export", json=[payload]).json()["path"])
    row = list(csv.reader(path.read_text(encoding="utf-8").splitlines()))[1]
    assert row[7] == "-0.0021"
