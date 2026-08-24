import numpy as np
import numpy.typing as npt

from pca.calibration import MeterConfig, SpectralData, UnitCalibration
from pca.device import DeviceNotFoundError, FakeSpectrometer, Spectrometer
from pca.engine import AVERAGE_COUNT, STABILITY_WINDOW, Engine, classify_stability

N = 32


def make_unit(wavelengths: npt.NDArray[np.float64]) -> UnitCalibration:
    dark = SpectralData(wavelengths, np.zeros(N), 1_000_000)
    lamp = SpectralData(wavelengths, np.full(N, 1e-6), 1_000_000)
    ref = SpectralData(wavelengths, np.zeros(N), 1_000_000)
    config = MeterConfig(
        boxcar=0, steradians=1.0, collection_area=1.0,
        agc_level=55_700, stable_tol=1_000, nl_correction=True, zero_candelas=0.0,
    )
    return UnitCalibration(dark, lamp, ref, config)


def make_engine(spectra: list[npt.NDArray[np.float64]]) -> Engine:
    wavelengths = np.linspace(380.0, 780.0, N)
    device = FakeSpectrometer(wavelengths, spectra)
    engine = Engine(make_unit(wavelengths), connect=lambda: device)
    engine.ensure_connected()
    return engine


def _fake_unit() -> UnitCalibration:
    return make_unit(np.linspace(380.0, 780.0, N))


def _flat_spectrum(unit: UnitCalibration, value: float = 27_850.0) -> npt.NDArray[np.float64]:
    return np.full(unit.dark.wavelengths.shape, value)


def test_engine_starts_disconnected_without_device() -> None:
    unit = _fake_unit()
    engine = Engine(
        unit, connect=lambda: FakeSpectrometer(unit.dark.wavelengths, [_flat_spectrum(unit)])
    )
    assert engine.connected is False
    assert engine.serial == ""
    assert engine.latest is None


def test_measure_produces_reading_and_agc_update() -> None:
    engine = make_engine([np.full(N, 27_850.0)])
    engine.set_averaging(False)
    measurement = engine.measure_once()
    assert measurement.reading.luminance_cdm2 > 0
    assert measurement.integration_us == 100_000
    assert engine.integration_us == 200_000
    assert engine.latest is measurement


def test_averaging_matches_single_read_for_constant_spectrum() -> None:
    spectrum = np.full(N, 27_850.0)
    single = make_engine([spectrum])
    single.set_averaging(False)
    single_result = single.measure_once()

    wavelengths = np.linspace(380.0, 780.0, N)
    device = FakeSpectrometer(wavelengths, [spectrum])
    averaged = Engine(make_unit(wavelengths), connect=lambda: device)
    averaged.ensure_connected()
    averaged_result = averaged.measure_once()

    assert averaged.integration_us == single.integration_us
    assert averaged_result.reading.luminance_cdm2 == single_result.reading.luminance_cdm2
    assert len(device.read_log) == AVERAGE_COUNT


def test_stability_stable_for_constant_luminance() -> None:
    engine = make_engine([np.full(N, 55_700.0)])
    engine.set_averaging(False)
    for _ in range(STABILITY_WINDOW):
        measurement = engine.measure_once()
    assert measurement.stability == "stable"
    assert measurement.stable is True
    assert measurement.variation_pct == 0.0


class ScaledFakeSpectrometer(FakeSpectrometer):
    """Real-hardware invariant: counts scale with integration, so a constant
    scene yields constant luminance (net / integration_us) while the AGC still
    changes integration_us on its way to the target peak."""

    def __init__(self, wavelengths: npt.NDArray[np.float64], base_at_ref: float) -> None:
        super().__init__(wavelengths, [np.zeros(N)])
        self._base = base_at_ref

    def read(self, integration_us: int) -> npt.NDArray[np.float64]:
        self.read_log.append(integration_us)
        return np.full(N, self._base * integration_us / 100_000)


def test_stability_reached_despite_integration_jitter() -> None:
    # Constant scene -> constant luminance, but the AGC keeps changing
    # integration_us on the way to target (peak starts far below 55_700).
    # Regression: integration jitter must NOT keep stability stuck on "acquiring".
    wavelengths = np.linspace(380.0, 780.0, N)
    device = ScaledFakeSpectrometer(wavelengths, 700.0)
    engine = Engine(make_unit(wavelengths), connect=lambda: device)
    engine.ensure_connected()
    engine.set_averaging(False)
    integrations = [engine.measure_once().integration_us for _ in range(STABILITY_WINDOW)]
    assert len(set(integrations)) > 1  # AGC jittered integration during the window
    assert engine.latest is not None
    assert engine.latest.stability == "stable"


def test_classify_stability_states() -> None:
    assert classify_stability([1.0, 1.0]) == ("acquiring", 0.0)
    assert classify_stability([100.0] * STABILITY_WINDOW)[0] == "stable"
    fluctuating = [100.0] * (STABILITY_WINDOW - 1) + [130.0]
    assert classify_stability(fluctuating)[0] == "fluctuating"
    assert classify_stability([0.0] * STABILITY_WINDOW) == ("acquiring", 0.0)


def test_saturation_flag() -> None:
    engine = make_engine([np.full(N, 65_535.0)])
    engine.set_averaging(False)
    assert engine.measure_once().saturated is True


def test_saturation_forces_fast_integration_descent() -> None:
    engine = make_engine([np.full(N, 65_535.0)])
    engine.set_averaging(False)
    engine.integration_us = 6_000_000
    engine.measure_once()
    assert engine.integration_us == 750_000


def test_runtime_dark_capture_and_clear() -> None:
    engine = make_engine([np.full(N, 100.0), np.full(N, 100.0)])
    engine.set_averaging(False)
    engine.capture_dark()
    measurement = engine.measure_once()
    assert measurement.reading.luminance_cdm2 == 0.0
    engine.clear_dark()


def test_scan_state() -> None:
    engine = make_engine([np.full(N, 1.0)])
    assert engine.scanning is True
    engine.stop()
    assert engine.scanning is False
    engine.start()
    assert engine.scanning is True


class FlakySpectrometer(FakeSpectrometer):
    def __init__(
        self, wavelengths: npt.NDArray[np.float64], spectra: list[npt.NDArray[np.float64]]
    ) -> None:
        super().__init__(wavelengths, spectra)
        self._raise_once = True

    def read(self, integration_us: int) -> npt.NDArray[np.float64]:
        if self._raise_once:
            self._raise_once = False
            raise RuntimeError("device unplugged")
        return super().read(integration_us)


def test_try_measure_flips_connected_on_error_and_recovery() -> None:
    wavelengths = np.linspace(380.0, 780.0, N)
    device = FlakySpectrometer(wavelengths, [np.full(N, 27_850.0)])
    engine = Engine(make_unit(wavelengths), connect=lambda: device)
    assert engine.ensure_connected() is True
    assert engine.connected is True
    assert engine.try_measure() is False
    assert engine.connected is False
    assert engine.try_measure() is True
    assert engine.connected is True


class DeadSpectrometer(FakeSpectrometer):
    """Simulates an unplugged device: every read fails on the same handle."""

    def __init__(self, wavelengths: npt.NDArray[np.float64]) -> None:
        super().__init__(wavelengths, [np.zeros(N)])
        self.closed = False

    def read(self, integration_us: int) -> npt.NDArray[np.float64]:
        raise RuntimeError("device unplugged")

    def close(self) -> None:
        self.closed = True


def test_try_measure_fails_when_current_device_is_dead() -> None:
    wavelengths = np.linspace(380.0, 780.0, N)
    device = DeadSpectrometer(wavelengths)
    engine = Engine(make_unit(wavelengths), connect=lambda: device)
    engine.ensure_connected()
    assert engine.try_measure() is False
    assert engine.connected is False


def test_ensure_connected_reopens_device_and_closes_old_one() -> None:
    wavelengths = np.linspace(380.0, 780.0, N)
    dead = DeadSpectrometer(wavelengths)
    healthy = FakeSpectrometer(wavelengths, [np.full(N, 27_850.0)])
    devices = iter([dead, healthy])
    engine = Engine(make_unit(wavelengths), connect=lambda: next(devices))
    engine.set_averaging(False)

    assert engine.ensure_connected() is True
    assert engine.try_measure() is False
    assert engine.connected is False

    assert engine.ensure_connected() is True
    assert engine.connected is True
    assert dead.closed is True

    assert engine.try_measure() is True
    assert engine.connected is True


def test_ensure_connected_stays_disconnected_when_still_unplugged() -> None:
    wavelengths = np.linspace(380.0, 780.0, N)
    dead = DeadSpectrometer(wavelengths)
    calls = {"n": 0}

    def factory() -> Spectrometer:
        calls["n"] += 1
        if calls["n"] == 1:
            return dead
        raise DeviceNotFoundError("no device")

    engine = Engine(make_unit(wavelengths), connect=factory)
    assert engine.ensure_connected() is True
    assert engine.try_measure() is False
    assert engine.ensure_connected() is False
    assert engine.connected is False


def test_ensure_connected_rejects_device_whose_grid_is_not_the_calibrated_one() -> None:
    unit = make_unit(np.linspace(380.0, 780.0, N))
    foreign = FakeSpectrometer(np.linspace(340.0, 1030.0, N), [np.full(N, 100.0)])
    engine = Engine(unit, connect=lambda: foreign)
    assert engine.ensure_connected() is False
    assert engine.connected is False
    assert engine.last_error is not None
    assert "GridMismatchError" in engine.last_error


def test_ensure_connected_rejects_and_closes_a_foreign_device() -> None:
    wavelengths = np.linspace(380.0, 780.0, N)
    dead = DeadSpectrometer(wavelengths)
    foreign = FakeSpectrometer(np.linspace(340.0, 1030.0, N), [np.full(N, 100.0)])
    closed: list[str] = []
    foreign.close = lambda: closed.append(foreign.serial)  # type: ignore[method-assign]
    devices = iter([dead, foreign])

    engine = Engine(make_unit(wavelengths), connect=lambda: next(devices))
    assert engine.ensure_connected() is True
    assert engine.try_measure() is False

    assert engine.ensure_connected() is False
    assert engine.connected is False
    assert closed == [foreign.serial]
    assert engine.last_error is not None
    assert "GridMismatchError" in engine.last_error


def test_last_error_records_and_clears() -> None:
    wavelengths = np.linspace(380.0, 780.0, N)
    device = FlakySpectrometer(wavelengths, [np.full(N, 27_850.0)])
    engine = Engine(make_unit(wavelengths), connect=lambda: device)
    assert engine.ensure_connected() is True
    assert engine.last_error is None
    assert engine.try_measure() is False
    assert engine.last_error == "RuntimeError: device unplugged"
    assert engine.try_measure() is True
    assert engine.last_error is None
