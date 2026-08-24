# PCA-100: DCI calibration suitability and limits

Date: 2026-07-24
Instrument: USL PCA-100 (Ocean Optics USB2000+ inside), unit 0302 (serial number F00302).
Measurements are taken as screen reflectance, as required by DCI/SMPTE.

## Summary

For **operational DCI alignment and verification** of xenon and laser-phosphor projectors, accuracy is sufficient and equivalent to the original USL application. The application was verified side-by-side against the original USL software on 2026-07-24; saturated colors were additionally improved relative to the original (see `validation-protocol.md`, dark model). The limitations described below apply to formal certification audits and to RGB laser.

## What DCI calibration checks and where we stand

| Quantity | DCI/SMPTE tolerance (indicative) | Our agreement | Verdict |
|---|---|---|---|
| White point (DCI white 0.314 / 0.351) | ±0.006 Δu'v', acceptance often ±0.002 x/y | +0.001 / +0.005 vs. original and D65 | OK |
| Luminance (48 cd/m² = 14 fL on screen) | ±10%, target ±5% | <0.5% on white, ~4% on colors | OK |
| Primaries vs. DCI-P3 gamut | ±0.010-0.015 Δxy | up to ~0.009 from reference | borderline-within tolerance |

## Limits and honest caveats

### 1. Relative agreement, not traceable calibration
The instrument is aligned with the original USL application and with theoretical P3 targets - excellent relative agreement, but this is NOT a calibration traceable to a national standard (NIST/PTB). Both absolute luminance and spectral sensitivity rest on the **factory calibration from 2009** (`lamp.bin`) - this applies equally to the old and to our application.

- Routine alignment, maintenance, auditorium checks: ready.
- Formal DCI acceptance certification of a new auditorium with a stamp: expects an instrument with a valid calibration certificate (annual recalibration at the manufacturer). Obtain a fresh recalibration before certification.

### 2. RGB laser projectors (Barco SP4K and similar)
Narrow laser primaries are at the edge of what the USB2000+ can handle (optical resolution + wavelength calibration accuracy ±0.3-0.5 nm). This limitation is HARDWARE-based and shared with the original USL application.

- Xenon (DP2K/DP4K) and laser phosphor (SP2K): measure well, full confidence.
- RGB laser (SP4K): white point and luminance reliably (the core of DCI compliance), individual laser primaries only indicatively.
- Reference per-primary chromaticity of RGB laser requires spectroradiometers with sub-nm accuracy (Colorimetry Research CR-250/300, JETI, Konica Minolta CS-2000).
- Optional refinement: a control scan of a fluorescent lamp (mercury lines at 435.8 / 546.1 / 611.6 nm) to fine-tune the instrument's wavelength calibration.

### 3. Absolute luminance in cd/m²
Relatively (white vs. colors, between levels) it is consistent. The absolute value relies on the 2009 factory lamp.

## Recommended workflow for a cinema

1. Instrument on a tripod, aimed at the designated screen spot, auditorium darkened.
2. Projector warmed up (xenon 10+ min stabilization).
3. White point and luminance at DCI white - primary check.
4. R/G/B (and CMY check colors) against the target gamut - full confidence for xenon/laser-phosphor, indicative for RGB laser.
5. On mismatch, see `validation-protocol.md`, known deviations section.

## Conclusion

Operational DCI alignment and verification of xenon and laser-phosphor projectors: yes, sufficient and equivalent to the original. Certification audit: obtain a fresh recalibration of the instrument. RGB laser: expect the primaries limitation imposed by the hardware.
