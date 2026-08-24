"""Spectrometer access. Bottom layer: imports nothing from pca."""
from typing import Protocol

import numpy as np
import numpy.typing as npt

INTEGRATION_LIMITS_US = (1_000, 6_000_000)


class DeviceNotFoundError(RuntimeError):
    pass


class Spectrometer(Protocol):
    serial: str
    saturation_level: float

    def wavelengths(self) -> npt.NDArray[np.float64]: ...
    def read(self, integration_us: int) -> npt.NDArray[np.float64]: ...
    def close(self) -> None: ...


class FakeSpectrometer:
    def __init__(
        self,
        wavelengths: npt.NDArray[np.float64],
        spectra: list[npt.NDArray[np.float64]],
        nl_correction: bool = True,
    ) -> None:
        self.serial = "FAKE-0001"
        self.saturation_level = 65_535.0
        self.read_log: list[int] = []
        self.nl_correction = nl_correction
        self._wavelengths = wavelengths
        self._spectra = spectra
        self._index = 0

    def wavelengths(self) -> npt.NDArray[np.float64]:
        return self._wavelengths

    def read(self, integration_us: int) -> npt.NDArray[np.float64]:
        self.read_log.append(integration_us)
        spectrum = self._spectra[self._index % len(self._spectra)]
        self._index += 1
        return spectrum

    def close(self) -> None:
        return None


class SeabreezeSpectrometer:
    def __init__(self, nl_correction: bool = True) -> None:
        from seabreeze.spectrometers import Spectrometer as SbSpectrometer

        try:
            self._device = SbSpectrometer.from_first_available()
        except Exception as exc:
            raise DeviceNotFoundError(str(exc)) from exc
        self.serial = str(self._device.serial_number)
        self.saturation_level = float(self._device.max_intensity)
        self._current_integration_us = 0
        self._nl_correction = nl_correction

    def wavelengths(self) -> npt.NDArray[np.float64]:
        return np.asarray(self._device.wavelengths(), dtype=np.float64)

    def read(self, integration_us: int) -> npt.NDArray[np.float64]:
        if integration_us != self._current_integration_us:
            self._device.integration_time_micros(integration_us)
            self._current_integration_us = integration_us
            # The acquisition already in flight was exposed with the previous
            # timing; discard it so the returned scan matches the requested
            # integration. Without this every retune feeds one stale scan
            # into the average and the luminance display jumps.
            self._device.intensities(
                correct_dark_counts=True, correct_nonlinearity=self._nl_correction
            )
        return np.asarray(
            self._device.intensities(
                correct_dark_counts=True, correct_nonlinearity=self._nl_correction
            ),
            dtype=np.float64,
        )

    def close(self) -> None:
        self._device.close()


def open_first_available(nl_correction: bool = True) -> Spectrometer:
    return SeabreezeSpectrometer(nl_correction)
