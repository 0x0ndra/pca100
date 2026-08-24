# Validation protocol - new application vs. old application PCA-100

Goal: verify measurement parity of the new application (macOS, `pca` backend +
Ocean Optics USB2000+ spectrometer) against the old application
(`PCA-100.exe`, Windows, same physical unit, unit 0302) on the same light
source. Without the table below filled in and signed off, the validation is
not considered complete.

## Already verified elsewhere (no need to repeat)

- Colorimetry against reference tabulated values (illuminant A, D65) -
  `backend/tests/test_colorimetry.py`.
- Calibration file parser against real data from unit 0302 -
  `backend/tests/test_calibration.py`.
- This protocol covers the remaining item: **side-by-side measurement against
  the old application on real hardware.**

## Setup

1. The old application runs on a Windows PC with a physically connected
   PCA-100. The new application runs on a Mac: `make dev` (backend on
   `:8320`, frontend on `:5175`, or directly `cd backend && uv run python -m
   pca.main`).
2. Both measurements target the **same light source** (projection screen /
   test patterns from the projector), same instrument distance and angle,
   darkened auditorium (no stray ambient light).
3. Before the first measurement, leave `ABSOLUTE_SCALE = 1.0` (default value
   in `backend/pca/pipeline.py`) - the calibration factor is determined first
   (see below), and only then is the full matrix measured.
4. Test patterns: white, red (R), green (G), blue (B), each at 3 brightness
   levels (e.g. 100 %, 50 %, low brightness with long integration - verifies
   AGC under long exposures).

## Match criteria

| Quantity | Tolerance |
|---|---|
| x (CIE 1931) | \|Δx\| <= 0.002 |
| y (CIE 1931) | \|Δy\| <= 0.002 |
| luminance (ft-L / cd/m2) | ±2 % |
| CCT | ±50 K |

A matrix row is **OK** only when it passes all four columns at once.

## Determining `ABSOLUTE_SCALE`

Both the old and new applications compute luminance from the same pipeline
(dark → boxcar → lamp curve → steradians/area), but the absolute scale can
differ by a constant factor. `ABSOLUTE_SCALE` in `backend/pca/pipeline.py`
compensates for this factor:

1. Measure a stable **white at 100 % brightness** on both applications (wait
   for the "Stable" indicator in the new app).
2. Record `old_luminance` (luminance from the old app, cd/m2) and
   `new_luminance` (luminance from the new app, field `luminance_cdm2` from
   `GET /api/measurement`).
3. Compute:

   ```
   ABSOLUTE_SCALE = old_luminance / new_luminance
   ```

4. Set this value as the `ABSOLUTE_SCALE` constant in
   `backend/pca/pipeline.py` (replace `1.0`).
5. Restart the backend (`make dev`, or `cd backend && uv run python -m
   pca.main`).
6. Measure white again - luminance should now match within ±2 %.
7. Go through the full matrix below and fill in the table.

## Measurement matrix (12 rows)

Fill in all cells for both applications, compute the deltas, and decide
pass/fail per the criteria above.

| Source | Brightness level | Old app luminance | Old app x | Old app y | Old app CCT | New app luminance | New app x | New app y | New app CCT | Δ luminance % | Δx | Δy | Δ CCT | Pass |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| White | 100 % |  |  |  |  |  |  |  |  |  |  |  |  |  |
| White | 50 % |  |  |  |  |  |  |  |  |  |  |  |  |  |
| White | low brightness |  |  |  |  |  |  |  |  |  |  |  |  |  |
| R | 100 % |  |  |  |  |  |  |  |  |  |  |  |  |  |
| R | 50 % |  |  |  |  |  |  |  |  |  |  |  |  |  |
| R | low brightness |  |  |  |  |  |  |  |  |  |  |  |  |  |
| G | 100 % |  |  |  |  |  |  |  |  |  |  |  |  |  |
| G | 50 % |  |  |  |  |  |  |  |  |  |  |  |  |  |
| G | low brightness |  |  |  |  |  |  |  |  |  |  |  |  |  |
| B | 100 % |  |  |  |  |  |  |  |  |  |  |  |  |  |
| B | 50 % |  |  |  |  |  |  |  |  |  |  |  |  |  |
| B | low brightness |  |  |  |  |  |  |  |  |  |  |  |  |  |

## On mismatch

1. Export the raw spectrum from the new application
   (`GET /api/measurement?spectrum=true` - returns `wavelengths` and
   `spectrum`) and the corresponding raw data from the old application for
   the same measurement.
2. Walk through the pipeline step by step (dark subtraction → boxcar
   smoothing → normalization to counts/s → lamp curve → steradians/area →
   `ABSOLUTE_SCALE`) and compare intermediate results between the two
   applications to locate the step where the values diverge.
3. Optionally: verify the formulas against the Ocean Optics SPAM library
   documentation (called by the old app via `SPAM64.dll`) as an independent
   reference.

## Known deviations from the old application

These differences are expected and are not bugs - keep them in mind when
diagnosing a mismatch in the matrix above, so they are not mistaken for
errors:

1. **Order of nonlinearity correction and dark subtraction.** New app:
   seabreeze applies electrical dark correction and nonlinearity correction
   (`correct_dark_counts`, `correct_nonlinearity`) directly in
   `intensities()`, i.e. BEFORE the `dark.bin` subtraction in
   `pca/pipeline.py::process`. The old app applied the steps in the opposite
   order: raw -> dark subtraction -> then nonlinearity. When diffing spectra
   (see the "On mismatch" section), this is the first step to suspect where
   intermediate results diverge.
2. **`scans_averaged`.** The new app does not average any scans (equivalent
   to a value of 1 - one readout = one measurement). The old app and unit
   0302's calibration files averaged 10 scans. This shows up as higher
   measurement noise between individual readouts in the new app, not a shift
   in the mean value - if you see a systematic deviation (not noise), look
   for the cause elsewhere.
3. **Semantics of `Boxcar` half-width.** The value and how it is applied
   (`half_width` -> window `2*half_width + 1`, see `boxcar_smooth` in
   `pca/pipeline.py`) is taken 1:1 from the SpectraSuite/Ocean Optics
   convention, not derived independently - if the old app used a different
   half-width-vs-full-window convention, this shows up as slight
   blurring/sharpening of the spectrum.

## Closeout

Validation is complete when all 12 rows of the matrix are **Pass**. Record
the final `ABSOLUTE_SCALE` value and the measurement date here:

- `ABSOLUTE_SCALE = `
- Date:
- Performed by:

## Calibration results 2026-07-24

Side-by-side measurement against the old application (`PCA-100.exe`) on unit
0302, source LCD monitor with W/R/G/B test patches, A-B-A bracketing (old -
new - old), to rule out source drift between measurements.

**Method:** White, red, green, and blue monitor patches measured by both
applications in an A-B-A loop (old app - new app - old app), to verify that
differences are not caused by monitor brightness fluctuation between
individual readouts.

**Missing step - normalization to CCD pixel width.** The pipeline (`process`
in `backend/pca/pipeline.py`) was missing the counts -> counts/nm conversion.
The spectral band width per pixel (delta-lambda) is not constant - for unit
0302 it is approximately 0.38 nm at the blue end of the spectrum and
approximately 0.29 nm at the red end. Without dividing by this value (via
`np.gradient` of the `unit.dark.wavelengths` wavelength grid), a mysterious
constant factor of about 2.88x versus the old application resulted. After
adding the division (`radiance /= np.gradient(unit.dark.wavelengths)`,
immediately after multiplying by the lamp curve, before dividing by
steradians), the absolute luminance matched the old app to within 3 %.

**White parity (100 % brightness):**

| Quantity | Old app | New app |
|---|---|---|
| luminance | exactly matched (by construction of `ABSOLUTE_SCALE`) | exactly matched |
| x | 0.3126 | 0.3120 |
| y | 0.3243 | 0.3220 |

**`ABSOLUTE_SCALE = 1.031318`.** Determined from the white patch: old app
44.977 ft-L, new app (with the new delta-lambda normalization, but still
without `ABSOLUTE_SCALE`) 43.6112 ft-L. `1.031318 = 44.977 / 43.6112`.

**Nonlinearity (NL) correction - default OFF.** The effective behavior of
the old application corresponds to seabreeze nonlinearity correction turned
off (the old app has its own, different NL handling). With NL correction
enabled in seabreeze, y shifts by -0.005 relative to the old app. Therefore
`pca/main.py` calls `open_first_available(nl_correction=False)`
unconditionally - `NLCorrection` in `colormeter.ini` still documents the old
application's intent, but does not control seabreeze's behavior.

**Known remaining deviation - saturated primary color (red).** For saturated
red, dx comes out to about -0.015 relative to the old app. Suspected cause:
the old app sampled the spectrum more coarsely (likely every 10 nm), while
the new app integrates every 1 nm, making it closer to physical reality for
narrowband/sharp-edged spectra. Under separate investigation (variant B).

**Note on calibration file serial numbers.** The factory calibration files
(year 2009) in `backend/data/0302/` carry the spectrometer serial number
`USB2+F01314` in the header, while the physical unit's label reads
`USB2+F00302`. These are the same files used by the old application - it is
a mismatch in the file header from the factory, not a misassigned
calibration; it has no effect on measurement parity.

## Dark model and recalibration 2026-07-24

**Finding.** Concurrent validation (MacBook XDR display in P3, unit F00302,
A-B-A scheme against the original USL application) showed that the
chromaticity of saturated colors was shifted (red x by -0.027, green y by
-0.039). The cause is a fixed sensor baseline offset of about 174 counts,
which the optically-black-pixel correction removes only partially, and the
linearly scaled factory `dark.bin` (year 2009, 1.575 s integration) does not
remove at all at short integration times (about 20 ms) - scaling it down
destroys the integration-independent component of the offset.

**Fix.** We captured a dark sweep (optics covered, 8 integration times from
3 ms to 1 s) and stored it as `backend/data/0302/dark_sweep.json`. These are
residual dark spectra AFTER the seabreeze electrically-black-pixel
correction, i.e. consistent with the pipeline input
(`correct_dark_counts=True`). The pipeline now interpolates the measured
dark linearly by integration time between the two neighboring captured
times (`modeled_dark` in `pca/pipeline.py`), clamping to the edge row outside
that range. When `dark_sweep.json` is absent, behavior falls back to the
original scaled `dark.bin`.

**New `ABSOLUTE_SCALE = 1.0466`** (redetermined 2026-07-24 with the dark
model, white P3 130.5 ft-L old app vs. our raw value). Replaces 1.031318.

**Agreement with the original application.** After subtracting the
interpolated measured dark, the chromaticity of both red and green matched
the original application to about 0.009 (previously 0.027 / 0.039), and
luminance to about 4 % after redetermining `ABSOLUTE_SCALE`. Acceptance
check: `backend/scripts/validate_darkmodel.py`.

| patch | ours x / y / ft-L | old app x / y / ft-L |
|---|---|---|
| white | 0.314 / 0.328 / 130.5 | 0.313 / 0.323 / 130.5 |
| red | 0.680 / 0.317 / 30.8 | 0.676 / 0.319 / 30.9 |
| green | 0.260 / 0.700 / 88.8 | 0.266 / 0.691 / 89.0 |
| blue | 0.151 / 0.056 / 10.1 | 0.152 / 0.059 / 10.5 |

**Scope of validity.** The dark sweep is specific to unit F00302, but
independent of the source (captured with the optics covered). If the unit is
replaced or the sensor drifts with temperature, a new dark sweep must be
captured.
