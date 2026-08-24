import { render } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { xyToSvg } from '@/lib/cie'
import { DEFAULT_CUSTOM, resolveReference, type ReferenceTarget } from '@/lib/dci-targets'
import type { Measurement } from '@/lib/types'
import { CIE_SIZE, CieDiagram } from './cie-diagram'

const DCI = resolveReference('dci', DEFAULT_CUSTOM, 14)
const REC709 = resolveReference('rec709', DEFAULT_CUSTOM, 14)

const base: Measurement = {
  luminance_ftl: 14.5,
  luminance_cdm2: 34.2,
  x: 0.31,
  y: 0.32,
  cct_k: 6500,
  duv: 0.001,
  integration_ms: 100,
  stable: true,
  stability: 'stable',
  variation_pct: 0.5,
  saturated: false,
  timestamp: '2026-07-23T00:00:00Z',
}

function corners(reference: ReferenceTarget): string {
  const { red, green, blue } = reference.primaries
  return [red, green, blue]
    .map((p) => {
      const { cx, cy } = xyToSvg(p.x, p.y, CIE_SIZE)
      return `${cx},${cy}`
    })
    .join(' ')
}

describe('CieDiagram', () => {
  it('draws the measured point at the xyToSvg-computed coordinates', () => {
    const { container } = render(
      <CieDiagram measurement={base} reference={DCI} showReference={false} />,
    )
    const point = container.querySelector('[data-testid="measured-point"]')
    expect(point).not.toBeNull()
    const { cx, cy } = xyToSvg(base.x, base.y, CIE_SIZE)
    expect(point?.getAttribute('cx')).toBe(String(cx))
    expect(point?.getAttribute('cy')).toBe(String(cy))
  })

  it('renders the clipped colored fill image', () => {
    const { container } = render(
      <CieDiagram measurement={null} reference={DCI} showReference={false} />,
    )
    const image = container.querySelector('[data-testid="cie-fill"]')
    expect(image?.getAttribute('href')).toBe('/cie-chromaticity.png')
    expect(image?.getAttribute('clip-path')).toBe('url(#cie-locus-clip)')
    expect(container.querySelector('clipPath#cie-locus-clip')).not.toBeNull()
  })

  it('hides the gamut triangle when showReference is false', () => {
    const { container } = render(
      <CieDiagram measurement={base} reference={DCI} showReference={false} />,
    )
    expect(container.querySelector('[data-testid="gamut-triangle"]')).toBeNull()
  })

  it('shows the gamut triangle when showReference is true', () => {
    const { container } = render(<CieDiagram measurement={base} reference={DCI} showReference />)
    expect(container.querySelector('[data-testid="gamut-triangle"]')).not.toBeNull()
  })

  it('draws the triangle and label of the selected reference, not always DCI', () => {
    const { container } = render(<CieDiagram measurement={base} reference={REC709} showReference />)
    const triangle = container.querySelector('[data-testid="gamut-triangle"]')
    expect(triangle?.getAttribute('points')).toBe(corners(REC709))
    expect(triangle?.getAttribute('points')).not.toBe(corners(DCI))
    expect(container.querySelector('[data-testid="gamut-label"]')?.textContent).toBe('Rec.709')
  })

  it('anchors the reference label to the reference white point', () => {
    const { container } = render(<CieDiagram measurement={null} reference={REC709} showReference />)
    const { cx } = xyToSvg(REC709.white.x, REC709.white.y, CIE_SIZE)
    expect(container.querySelector('[data-testid="gamut-label"]')?.getAttribute('x')).toBe(
      String(cx + 9),
    )
  })
})
