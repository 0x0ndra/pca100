import { fireEvent, render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { evaluateDci } from '@/lib/dci'
import {
  DEFAULT_CUSTOM,
  resolveReference,
  type ReferenceControl,
  type ReferenceKey,
} from '@/lib/dci-targets'
import { DciCompliance } from './dci-compliance'

function control(overrides: Partial<ReferenceControl> = {}): ReferenceControl {
  const key: ReferenceKey = overrides.key ?? 'dci'
  return {
    key,
    reference: resolveReference(key, DEFAULT_CUSTOM, 14),
    custom: DEFAULT_CUSTOM,
    rec709Lum: 14,
    onSelect: vi.fn(),
    onCustomChange: vi.fn(),
    onRec709LumChange: vi.fn(),
    ...overrides,
  }
}

const dci = resolveReference('dci', DEFAULT_CUSTOM, 14)
const whiteResult = evaluateDci(0.314, 0.351, 14.0, dci)

describe('DciCompliance', () => {
  it('shows a placeholder when there is no result', () => {
    render(<DciCompliance result={null} control={control()} />)
    expect(screen.getByText('Point the meter at a calibration color')).toBeInTheDocument()
  })

  it('renders the detected target label and a status badge', () => {
    render(<DciCompliance result={whiteResult} control={control()} />)
    expect(screen.getByText('Target: white')).toBeInTheDocument()
    expect(screen.getAllByText('Pass').length).toBeGreaterThan(0)
    expect(screen.getByText('Luminance')).toBeInTheDocument()
  })

  it('renders the four reference options in the selector', () => {
    render(<DciCompliance result={whiteResult} control={control()} />)
    for (const label of ['DCI', 'P3-D65', 'Rec.709', 'Custom']) {
      expect(screen.getByRole('button', { name: label })).toBeInTheDocument()
    }
  })

  it('calls onSelect when a reference is chosen', () => {
    const onSelect = vi.fn()
    render(<DciCompliance result={whiteResult} control={control({ onSelect })} />)
    fireEvent.click(screen.getByRole('button', { name: 'Custom' }))
    expect(onSelect).toHaveBeenCalledWith('custom')
  })

  it('reveals x/y/luminance inputs when Custom is active', () => {
    render(<DciCompliance result={whiteResult} control={control({ key: 'custom' })} />)
    expect(screen.getByText('white x')).toBeInTheDocument()
    expect(screen.getByText('white y')).toBeInTheDocument()
    expect(screen.getByText('lum (fL)')).toBeInTheDocument()
  })
})
