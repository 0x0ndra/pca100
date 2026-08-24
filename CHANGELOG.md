# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.1.1] - 2026-09-30

### Added

- CSV export of the measurement history: an "Export CSV" button in the
  history card saves the file to Downloads and reveals it in Finder.
- Measured values can be selected and copied (Cmd+C) in the app window.
- Luminance is shown with three decimals.

### Fixed

- Luminance no longer jumps by up to about 1 fL on a steady source. The
  automatic gain control retuned on small drift and each retune mixed one
  scan exposed with the previous integration time into the average; it now
  holds the integration time near its target and discards the first scan
  after a change.
- Measurement history is kept when the app is closed.

## [1.1.0] - 2026-08-24

### Added

- In-app update check: on startup the app queries GitHub Releases and, if a
  newer version is available, offers a one-click download of the signed
  DMG. Opt out with `PCA_NO_UPDATE_CHECK=1`.
- Remote-access toggle in the app: off by default (local-only, loopback
  bind). Enabling it binds the API to the LAN and shows a connect URL and
  QR code for a phone or second machine; disabling it rebinds to loopback.
  The toggle takes effect immediately, with no restart.
- Signing identity for packaging is now read from the `CODESIGN_IDENTITY`
  environment variable instead of being hardcoded in the build scripts.

### Changed

- Origin/Host guard hardening: the allow-list now accepts loopback and
  private/LAN IP addresses only, and no longer trusts DNS names such as
  `.local`/`.lan`/`.home`/`.internal`, which could be rebound to the
  operator's machine after the browser's same-origin check passed. A
  Host-header check now runs on every request, including the `/api/live`
  WebSocket handshake, closing DNS-rebinding attacks an Origin-only check
  would miss.
- The frontend Vite dev server now defaults to binding localhost instead of
  every interface, since the dev proxy has no auth of its own; set
  `PCA_DEV_LAN=1` to expose it on the LAN.

### Fixed

- Dark-sweep calibration rows are now validated against the unit's dark
  grid before use, instead of failing later during measurement.

## [1.0.0] - 2026-08-24

Initial public release.

### Added

- Live measurement of luminance (ft-L / cd/m² toggle), CIE 1931 x/y
  chromaticity, CCT, and ΔUV, with switchable scan averaging and a
  Settling / Fluctuating / Stable measurement stability indicator.
- CIE 1931 chromaticity diagram with a colored spectral fill, the selected
  reference gamut and white point overlaid, and the live measured point.
- Live spectrum plot with a wavelength-based color palette, scaled to the
  visible band.
- DCI/SMPTE compliance evaluation per SMPTE RP 431-2:2011, with a
  selectable reference (DCI / P3-D65 / Rec.709 / custom white point,
  luminance, and primaries) and a color-coded pass/marginal/fail readout.
- Measurement history with date, time, and an optional note, persisted
  across reloads.
- English and Czech UI strings (`lib/strings.ts`), including number and
  date formatting; the language is selectable from a dropdown in the header,
  persisted across launches, with English as the default.
- Instrument connection indicator with automatic reconnect after a USB
  disconnect, and error detail surfaced via `/api/status`.
- Runtime dark measurement ("Measure dark" / "Clear dark") and Scan
  On/Off, with state held by the backend.
- Native macOS desktop app (PyInstaller + pywebview), signed and
  notarized, distributed as a `.dmg` (Apple Silicon only).
- Onboarding flow for first-run calibration setup, reading per-unit
  calibration files from Application Support without requiring a restart.
- Measured dark model and absolute scale correction, validated
  side-by-side against the original USL PCA-100 software (see
  `docs/validation-protocol.md`).
- Backend layering enforced by import-linter (device -> calibration ->
  pipeline/colorimetry/agc -> engine -> api) and a 300-line-of-code cap per
  source file.
