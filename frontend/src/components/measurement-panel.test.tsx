import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Measurement } from '@/lib/types'
import { MeasurementPanel } from './measurement-panel'

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

describe('MeasurementPanel', () => {
  it('renders the Jas label and formatted luminance for the active unit', () => {
    render(<MeasurementPanel measurement={base} unit="cdm2" onToggleUnit={() => {}} />)
    expect(screen.getByText('Luminance')).toBeInTheDocument()
    expect(screen.getByText('34.200')).toBeInTheDocument()
  })

  it('calls onToggleUnit when the unit toggle is clicked', () => {
    const onToggleUnit = vi.fn()
    render(<MeasurementPanel measurement={base} unit="cdm2" onToggleUnit={onToggleUnit} />)
    fireEvent.click(screen.getByRole('button', { name: /unit/i }))
    expect(onToggleUnit).toHaveBeenCalledOnce()
  })

  it('shows the Saturated badge when the reading is saturated', () => {
    render(
      <MeasurementPanel
        measurement={{ ...base, saturated: true }}
        unit="cdm2"
        onToggleUnit={() => {}}
      />,
    )
    expect(screen.getByText('Saturated')).toBeInTheDocument()
  })

  it('renders the Stable badge with variation for a stable reading', () => {
    render(<MeasurementPanel measurement={base} unit="cdm2" onToggleUnit={() => {}} />)
    expect(screen.getByText('Stable')).toBeInTheDocument()
    expect(screen.getByText('±0.5 %')).toBeInTheDocument()
  })

  it('renders the Ustaluji badge and hides variation while acquiring', () => {
    render(
      <MeasurementPanel
        measurement={{ ...base, stability: 'acquiring', variation_pct: 0 }}
        unit="cdm2"
        onToggleUnit={() => {}}
      />,
    )
    expect(screen.getByText('Acquiring…')).toBeInTheDocument()
    expect(screen.queryByText(/%/)).not.toBeInTheDocument()
  })

  it('renders the Fluctuating badge for a fluctuating reading', () => {
    render(
      <MeasurementPanel
        measurement={{ ...base, stability: 'fluctuating', variation_pct: 3.2 }}
        unit="cdm2"
        onToggleUnit={() => {}}
      />,
    )
    expect(screen.getByText('Fluctuating')).toBeInTheDocument()
    expect(screen.getByText('±3.2 %')).toBeInTheDocument()
  })
})

describe('MeasurementPanel luminance color-coding', () => {
  it('uses the default accent color when there is no luminance verdict', () => {
    const { container } = render(
      <MeasurementPanel measurement={base} unit="cdm2" onToggleUnit={() => {}} />,
    )
    const value = container.querySelector('[data-status]')
    expect(value).toHaveAttribute('data-status', 'none')
    expect(value?.className).toContain('text-primary')
  })

  it.each([
    ['ok', 'text-emerald-400'],
    ['marginal', 'text-amber-400'],
    ['out', 'text-destructive'],
  ] as const)('colors the big number for %s luminance status', (status, cls) => {
    const { container } = render(
      <MeasurementPanel
        measurement={base}
        unit="cdm2"
        onToggleUnit={() => {}}
        luminanceStatus={status}
      />,
    )
    const value = container.querySelector('[data-status]')
    expect(value).toHaveAttribute('data-status', status)
    expect(value?.className).toContain(cls)
  })

  it('renders the luminance legend', () => {
    render(<MeasurementPanel measurement={base} unit="cdm2" onToggleUnit={() => {}} />)
    expect(screen.getByText('in tolerance')).toBeInTheDocument()
    expect(screen.getByText('marginal')).toBeInTheDocument()
    expect(screen.getByText('out')).toBeInTheDocument()
  })
})
