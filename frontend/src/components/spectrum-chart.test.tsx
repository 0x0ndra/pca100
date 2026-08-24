import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { linePath, visiblePoints } from '@/lib/spectrum'
import type { Measurement } from '@/lib/types'
import { SpectrumChart } from './spectrum-chart'

function measurementWith(wavelengths: number[], spectrum: number[]): Measurement {
  return {
    luminance_ftl: 14,
    luminance_cdm2: 48,
    x: 0.314,
    y: 0.351,
    cct_k: 6300,
    duv: 0.001,
    integration_ms: 100,
    stable: true,
    stability: 'stable',
    variation_pct: 0.2,
    saturated: false,
    timestamp: '2026-07-25T00:00:00Z',
    wavelengths,
    spectrum,
  }
}

describe('SpectrumChart', () => {
  it('plots only the in-band samples of the full spectrometer grid', () => {
    const wavelengths = [339.68, 400, 550, 700, 1028.98]
    const spectrum = [900, 10, 100, 10, 5000]
    const { container } = render(
      <SpectrumChart measurement={measurementWith(wavelengths, spectrum)} />,
    )
    expect(container.querySelector('[data-testid="spectrum-line"]')?.getAttribute('d')).toBe(
      linePath(visiblePoints(wavelengths, spectrum)),
    )
  })

  it('falls back to the empty state when no sample lands in the band', () => {
    const { container, getByText } = render(
      <SpectrumChart measurement={measurementWith([900, 1000], [1, 2])} />,
    )
    expect(container.querySelector('[data-testid="spectrum-line"]')).toBeNull()
    expect(getByText('Spectrum not available')).toBeTruthy()
  })

  it('shows the empty state without a measurement', () => {
    const { getByText } = render(<SpectrumChart measurement={null} />)
    expect(getByText('Spectrum not available')).toBeTruthy()
  })
})
