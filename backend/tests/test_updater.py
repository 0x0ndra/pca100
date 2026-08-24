import json
from pathlib import Path
from urllib.error import URLError

import pytest

import pca
from pca import updater


def _fake_release(tag: str, dmg_url: str = "https://example.com/PCA-100-1.2.0.dmg") -> bytes:
    return json.dumps(
        {
            "tag_name": tag,
            "html_url": "https://github.com/0x0ndra/pca100/releases/tag/" + tag,
            "assets": [{"browser_download_url": dmg_url, "name": "PCA-100-1.2.0.dmg"}],
        }
    ).encode()


class _FakeResponse:
    def __init__(self, data: bytes) -> None:
        self._data = data

    def read(self, size: int = -1) -> bytes:
        data, self._data = self._data, b""
        return data if size < 0 else data[:size]

    def __enter__(self) -> "_FakeResponse":
        return self

    def __exit__(self, *exc: object) -> None:
        return None


def test_newer_version_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pca, "__version__", "1.1.0")
    monkeypatch.setattr(updater, "_fetch_latest_release", lambda timeout: _fake_release("v1.2.0"))
    info = updater.check_latest()
    assert info.available is True
    assert info.latest == "1.2.0"
    assert info.error is None
    assert info.release_url is not None


def test_equal_version_not_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pca, "__version__", "1.1.0")
    monkeypatch.setattr(updater, "_fetch_latest_release", lambda timeout: _fake_release("v1.1.0"))
    info = updater.check_latest()
    assert info.available is False
    assert info.error is None


def test_older_latest_not_available(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pca, "__version__", "1.1.0")
    monkeypatch.setattr(updater, "_fetch_latest_release", lambda timeout: _fake_release("v1.0.0"))
    info = updater.check_latest()
    assert info.available is False


def test_short_version_string_compares(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pca, "__version__", "1.1.0")
    monkeypatch.setattr(updater, "_fetch_latest_release", lambda timeout: _fake_release("v1.1"))
    info = updater.check_latest()
    assert info.available is False
    assert info.error is None


def test_malformed_tag_returns_error_not_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pca, "__version__", "1.1.0")
    monkeypatch.setattr(
        updater, "_fetch_latest_release", lambda timeout: _fake_release("not-a-version")
    )
    info = updater.check_latest()
    assert info.available is False
    assert info.error is not None


def test_network_failure_returns_error_not_crash(monkeypatch: pytest.MonkeyPatch) -> None:
    def _raise(timeout: float) -> bytes:
        raise URLError("boom")

    monkeypatch.setattr(updater, "_fetch_latest_release", _raise)
    info = updater.check_latest()
    assert info.available is False
    assert info.error is not None
    assert info.latest is None


def test_no_update_check_env_short_circuits(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("PCA_NO_UPDATE_CHECK", "1")

    def _fail(timeout: float) -> bytes:
        raise AssertionError("must not hit the network")

    monkeypatch.setattr(updater, "_fetch_latest_release", _fail)
    info = updater.check_latest()
    assert info.available is False
    assert info.error is None
    assert info.latest is None


def test_current_version_carried_through(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pca, "__version__", "1.1.0")
    monkeypatch.setattr(updater, "_fetch_latest_release", lambda timeout: _fake_release("v1.2.0"))
    info = updater.check_latest()
    assert info.current == "1.1.0"


def test_asset_url_extracted_from_dmg_asset(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(pca, "__version__", "1.1.0")
    monkeypatch.setattr(
        updater,
        "_fetch_latest_release",
        lambda timeout: _fake_release("v1.2.0", "https://example.com/PCA-100-1.2.0.dmg"),
    )
    info = updater.check_latest()
    assert info.asset_url == "https://example.com/PCA-100-1.2.0.dmg"


def test_download_dmg_rejects_non_pca_filename(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="PCA-100"):
        updater.download_dmg("https://example.com/evil.dmg", dest_dir=tmp_path)


def test_download_dmg_streams_to_dest_dir(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(updater, "_open_url", lambda url, timeout: _FakeResponse(b"dmg-bytes"))
    path = updater.download_dmg("https://example.com/PCA-100-1.2.0.dmg", dest_dir=tmp_path)
    assert path == tmp_path / "PCA-100-1.2.0.dmg"
    assert path.read_bytes() == b"dmg-bytes"
