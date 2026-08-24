from pca import resources

REQUIRED = ("dark.bin", "lamp.bin", "reference.bin", "colormeter.ini")


def test_calibration_absent_then_present(tmp_path, monkeypatch):
    cal = tmp_path / "calibration"
    monkeypatch.setattr(resources, "_CALIBRATION_DIR", cal)
    assert resources.calibration_present() is False
    resources.calibration_dir().mkdir(parents=True, exist_ok=True)
    for name in REQUIRED:
        (cal / name).write_text("x", encoding="utf-8")
    assert resources.calibration_present() is True


def test_dev_frontend_dir_points_to_dist(monkeypatch):
    monkeypatch.setattr(resources, "is_frozen", lambda: False)
    assert resources.resource_frontend_dir().name == "dist"
