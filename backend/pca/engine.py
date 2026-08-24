"""Measurement loop: device -> pipeline -> colorimetry, with AGC and scan state."""
import asyncio
import collections
import contextlib
import threading
from collections.abc import Callable, Sequence
from dataclasses import dataclass, field
from datetime import UTC, datetime
from pathlib import Path

import numpy as np
import numpy.typing as npt

from pca.agc import is_saturated, next_integration_us
from pca.calibration import SpectralData, UnitCalibration
from pca.colorimetry import ColorReading, spectrum_to_reading
from pca.device import INTEGRATION_LIMITS_US, DeviceNotFoundError, Spectrometer
from pca.pipeline import assert_compatible_grid, process
from pca.updater import UpdateInfo

INITIAL_INTEGRATION_US = 100_000
AVERAGE_COUNT = 8
STABILITY_WINDOW = 6
STABLE_REL_TOLERANCE = 0.01


def classify_stability(history: Sequence[float]) -> tuple[str, float]:
    if len(history) < STABILITY_WINDOW:
        return "acquiring", 0.0
    mean = sum(history) / len(history)
    if mean <= 0:
        return "acquiring", 0.0
    spread = (max(history) - min(history)) / mean
    stability = "stable" if spread <= STABLE_REL_TOLERANCE else "fluctuating"
    return stability, spread * 100


@dataclass(frozen=True)
class Measurement:
    reading: ColorReading
    integration_us: int
    stable: bool
    stability: str
    variation_pct: float
    saturated: bool
    timestamp: datetime
    wavelengths: npt.NDArray[np.float64]
    spectrum: npt.NDArray[np.float64]


class Engine:
    def __init__(
        self,
        unit: UnitCalibration,
        connect: Callable[[], Spectrometer],
    ) -> None:
        self._unit = unit
        self._connect_factory = connect
        self._lock = threading.Lock()
        self._device: Spectrometer | None = None
        self._wavelengths: npt.NDArray[np.float64] | None = None
        self._runtime_dark: SpectralData | None = None
        self._history: collections.deque[float] = collections.deque(maxlen=STABILITY_WINDOW)
        self.integration_us = INITIAL_INTEGRATION_US
        self.averaging = True
        self.scanning = True
        self.latest: Measurement | None = None
        self.connected = False
        self.last_error: str | None = None

    @property
    def serial(self) -> str:
        return self._device.serial if self._device is not None else ""

    @property
    def dark_active(self) -> bool:
        return self._runtime_dark is not None

    def ensure_connected(self) -> bool:
        if self.connected and self._device is not None:
            return True
        with self._lock:
            with contextlib.suppress(Exception):
                if self._device is not None:
                    self._device.close()
            device: Spectrometer | None = None
            try:
                device = self._connect_factory()
                wavelengths = device.wavelengths()
                assert_compatible_grid(wavelengths, self._unit)
            except Exception as exc:
                with contextlib.suppress(Exception):
                    if device is not None:
                        device.close()
                return self._fail(exc)
            self._device = device
            self._wavelengths = wavelengths
            self.connected = True
            self.last_error = None
            return True

    def set_averaging(self, enabled: bool) -> None:
        self.averaging = enabled

    def start(self) -> None:
        self.scanning = True

    def stop(self) -> None:
        self.scanning = False

    def capture_dark(self) -> None:
        with self._lock:
            if self._device is None or self._wavelengths is None:
                raise DeviceNotFoundError("no device connected")
            raw = self._device.read(self.integration_us)
            self._runtime_dark = SpectralData(self._wavelengths, raw, self.integration_us)

    def clear_dark(self) -> None:
        with self._lock:
            self._runtime_dark = None

    def close(self) -> None:
        with self._lock:
            with contextlib.suppress(Exception):
                if self._device is not None:
                    self._device.close()
            self._device = None
            self._wavelengths = None
            self.connected = False

    def _read_raw(self, device: Spectrometer, integration_us: int) -> npt.NDArray[np.float64]:
        if not self.averaging:
            return device.read(integration_us)
        reads = [device.read(integration_us) for _ in range(AVERAGE_COUNT)]
        return np.mean(reads, axis=0)

    def _track_stability(self, luminance: float) -> tuple[str, float]:
        self._history.append(luminance)
        return classify_stability(self._history)

    def measure_once(self) -> Measurement:
        with self._lock:
            if self._device is None or self._wavelengths is None:
                raise DeviceNotFoundError("no device connected")
            device = self._device
            wavelengths = self._wavelengths
            integration_us = self.integration_us
            raw = self._read_raw(device, integration_us)
            peak = float(np.max(raw))
            saturated = is_saturated(peak, device.saturation_level)
            self.integration_us = next_integration_us(
                peak,
                integration_us,
                self._unit.config.agc_level,
                INTEGRATION_LIMITS_US,
                saturated=saturated,
            )
            spectrum = process(raw, integration_us, self._unit, self._runtime_dark)
            reading = spectrum_to_reading(wavelengths, spectrum)
            stability, variation_pct = self._track_stability(reading.luminance_cdm2)
            measurement = Measurement(
                reading=reading,
                integration_us=integration_us,
                stable=stability == "stable",
                stability=stability,
                variation_pct=variation_pct,
                saturated=saturated,
                timestamp=datetime.now(UTC),
                wavelengths=wavelengths,
                spectrum=spectrum,
            )
            self.latest = measurement
            return measurement

    def _fail(self, exc: Exception) -> bool:
        self.connected = False
        self.last_error = f"{type(exc).__name__}: {exc}"
        return False

    def try_measure(self) -> bool:
        try:
            self.measure_once()
        except Exception as exc:
            return self._fail(exc)
        self.connected = True
        self.last_error = None
        return True


@dataclass
class DownloadState:
    state: str = "idle"  # idle | downloading | downloaded | error
    error: str | None = None
    path: Path | None = None


@dataclass
class AppState:
    engine: "Engine | None"
    load_engine: Callable[[], "Engine | None"]
    calibration_dir: Path
    remote_access: bool = False
    port: int = 8320
    on_remote_access_change: Callable[[bool], None] | None = None
    update_info: UpdateInfo | None = None
    download: DownloadState = field(default_factory=DownloadState)


async def run_loop(state: AppState, interval_s: float = 0.0) -> None:
    while True:
        engine = state.engine
        if engine is None or not engine.scanning:
            await asyncio.sleep(0.2)
            continue
        if not engine.connected:
            if not await asyncio.to_thread(engine.ensure_connected):
                await asyncio.sleep(2.0)
            continue
        if not await asyncio.to_thread(engine.try_measure):
            await asyncio.sleep(2.0)
            continue
        if interval_s:
            await asyncio.sleep(interval_s)
