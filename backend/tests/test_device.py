import numpy as np

from pca.device import FakeSpectrometer, Spectrometer


def test_fake_cycles_and_logs() -> None:
    wavelengths = np.linspace(340, 1029, 16)
    a, b = np.full(16, 1.0), np.full(16, 2.0)
    fake: Spectrometer = FakeSpectrometer(wavelengths, [a, b])
    assert np.array_equal(fake.read(10_000), a)
    assert np.array_equal(fake.read(20_000), b)
    assert np.array_equal(fake.read(30_000), a)
    assert fake.read_log == [10_000, 20_000, 30_000]
    assert fake.serial == "FAKE-0001"
    assert fake.saturation_level == 65_535.0


def test_seabreeze_discards_first_scan_after_integration_change() -> None:
    from pca.device import SeabreezeSpectrometer

    class StubDevice:
        def __init__(self) -> None:
            self.calls: list[tuple[object, ...]] = []

        def integration_time_micros(self, us: int) -> None:
            self.calls.append(("set", us))

        def intensities(self, **_: object) -> list[float]:
            self.calls.append(("read",))
            return [1.0]

    spec = object.__new__(SeabreezeSpectrometer)
    stub = StubDevice()
    spec._device = stub
    spec._current_integration_us = 0
    spec._nl_correction = False

    spec.read(100_000)
    assert stub.calls == [("set", 100_000), ("read",), ("read",)]

    stub.calls.clear()
    spec.read(100_000)
    assert stub.calls == [("read",)]


def test_fake_records_nl_correction_flag() -> None:
    wavelengths = np.linspace(340, 1029, 16)
    default_flag = FakeSpectrometer(wavelengths, [np.full(16, 1.0)])
    assert default_flag.nl_correction is True

    disabled = FakeSpectrometer(wavelengths, [np.full(16, 1.0)], nl_correction=False)
    assert disabled.nl_correction is False
