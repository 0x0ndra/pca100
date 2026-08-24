import json

import pca.settings as settings


def test_defaults_false_when_missing(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "_SETTINGS_PATH", tmp_path / "settings.json")
    assert settings.get_remote_access() is False


def test_roundtrip(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "_SETTINGS_PATH", tmp_path / "settings.json")
    settings.set_remote_access(True)
    assert settings.get_remote_access() is True
    assert json.loads((tmp_path / "settings.json").read_text())["remote_access"] is True


def test_corrupt_file_defaults_false(tmp_path, monkeypatch) -> None:
    p = tmp_path / "settings.json"
    p.write_text("{ not json")
    monkeypatch.setattr(settings, "_SETTINGS_PATH", p)
    assert settings.get_remote_access() is False


def test_settings_path_exposes_location(tmp_path, monkeypatch) -> None:
    monkeypatch.setattr(settings, "_SETTINGS_PATH", tmp_path / "settings.json")
    assert settings.settings_path() == tmp_path / "settings.json"
