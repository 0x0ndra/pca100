# Bring your own calibration

PCA-100 does not ship with calibration data. This is intentional: the
calibration files describe one physical instrument, not the software.
Using another unit's files produces plausible-looking but wrong readings,
so you supply your own.

## Why calibration is per-unit

`dark.bin` and `lamp.bin` are measured at the factory for a specific
spectrometer: the sensor's pixel-to-wavelength grid and its per-pixel
response. The processing pipeline subtracts the stored dark spectrum and
multiplies by the stored lamp spectrum element-wise, pixel for pixel. A
different unit with the same pixel count would broadcast through that math
without error and produce a result that looks like a valid measurement but
is not - there is no runtime error to warn you.

To guard against this, the app checks the wavelength grid reported by the
connected device against the grid recorded in your calibration on every
startup and every reconnect. If they don't match within tolerance, the app
refuses to trust the measurement rather than silently mixing calibrations
from two different units.

## Where to find your files

Your PCA-100 unit shipped with the original USL Windows software, which was
set up with a calibration for that specific unit at installation or at the
factory. On the Windows PC that has run the USL software, the installer
places the calibration in a folder named after your unit number:

```
C:\Program Files\USL\PCA-100\<unit number>\
```

For example, unit 0302 keeps its files in
`C:\Program Files\USL\PCA-100\0302\`. Copy the files below out of that
folder (it also contains `secondary.csv` and chart images, which this app
does not use). These are the same files the original software reads -
PCA-100 does not recompute or regenerate them.

## Required files

All four of these must be present, or the app treats calibration as not
installed:

- `dark.bin`
- `lamp.bin`
- `reference.bin`
- `colormeter.ini`

## Optional file

- `dark_sweep.json` - a measured dark model captured across several
  integration times. When present, the app interpolates the dark spectrum
  by integration time instead of linearly scaling a single reference dark,
  which improves accuracy at short integration times. When absent, the app
  falls back to scaling `dark.bin`. See `docs/validation-protocol.md` for
  the background on why this matters and how to capture one. This file is
  not part of the original USL installation - you only have it if you (or
  a previous validation pass) generated it.

## Where to put them

Copy all files into:

```
~/Library/Application Support/PCA-100/calibration/
```

The app creates this folder on first launch if it doesn't already exist.

## What happens if files are missing

On startup, if any of the four required files are missing, the app shows
an onboarding screen instead of the measurement view. It lists the missing
folder and required file names, and offers a button to open the folder in
Finder so you can drop the files in directly. The backend also reports
calibration as not present to any API caller during this state.

## Reloading after copying files

Once the files are in place, use the "Load calibration" action on the
onboarding screen. This calls `POST /api/calibration/reload` on the
backend, which re-reads the calibration directory and, if all four
required files are now present and valid, switches the app into the
measurement view - no restart needed. If the reload still reports missing
or invalid files, re-check the folder path and file names and try again.
