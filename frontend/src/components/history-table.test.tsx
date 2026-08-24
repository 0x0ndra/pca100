import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { formatTimestamp } from '@/lib/format'
import type { Measurement } from '@/lib/types'
import { useHistoryExport } from '@/hooks/use-history-export'
import { HistoryTable, type HistoryEntry } from './history-table'

vi.mock('@/hooks/use-history-export', () => ({ useHistoryExport: vi.fn() }))

function mockExport(overrides: Partial<ReturnType<typeof useHistoryExport>> = {}) {
  const exportCsv = vi.fn()
  vi.mocked(useHistoryExport).mockReturnValue({
    exportCsv,
    pending: false,
    error: null,
    lastPath: null,
    ...overrides,
  })
  return exportCsv
}

beforeEach(() => {
  mockExport()
})

const iso = '2026-07-24T13:42:03Z'

const measurement: Measurement = {
  luminance_ftl: 14.0,
  luminance_cdm2: 48,
  x: 0.314,
  y: 0.351,
  cct_k: 6300,
  duv: 0,
  integration_ms: 100,
  stable: true,
  stability: 'stable',
  variation_pct: 0.2,
  saturated: false,
  timestamp: iso,
}

const entries: HistoryEntry[] = [{ id: 1, label: 'White', note: 'screen center', measurement }]

describe('HistoryTable', () => {
  it('renders a locale date and time for a saved entry', () => {
    render(<HistoryTable entries={entries} onSave={() => {}} onClear={() => {}} />)
    expect(screen.getByText(formatTimestamp(iso))).toBeInTheDocument()
    expect(screen.getByText(formatTimestamp(iso))).toHaveTextContent('2026')
  })

  it('shows the note of a saved entry', () => {
    render(<HistoryTable entries={entries} onSave={() => {}} onClear={() => {}} />)
    expect(screen.getByText('screen center')).toBeInTheDocument()
  })

  it('shows luminance in both fL and cd/m², fL first', () => {
    render(<HistoryTable entries={entries} onSave={() => {}} onClear={() => {}} />)
    const headers = screen.getAllByRole('columnheader').map((h) => h.textContent)
    expect(headers.indexOf('fL')).toBeGreaterThan(-1)
    expect(headers.indexOf('fL')).toBeLessThan(headers.indexOf('cd/m²'))
    expect(screen.getByText('14.000')).toBeInTheDocument()
    expect(screen.getByText('48.000')).toBeInTheDocument()
  })

  it('keeps same-label entries as distinct rows', () => {
    const repeated: HistoryEntry[] = [
      { id: 2, label: 'White', note: '', measurement },
      { id: 1, label: 'White', note: '', measurement },
    ]
    render(<HistoryTable entries={repeated} onSave={() => {}} onClear={() => {}} />)
    expect(screen.getAllByText('White')).toHaveLength(2)
  })

  it('passes the typed name and note to onSave', () => {
    const onSave = vi.fn()
    render(<HistoryTable entries={[]} onSave={onSave} onClear={() => {}} />)
    fireEvent.change(screen.getByPlaceholderText('Measurement name'), {
      target: { value: 'White' },
    })
    fireEvent.change(screen.getByPlaceholderText('Note (optional)'), {
      target: { value: 'after calibration' },
    })
    screen.getByRole('button', { name: 'Save measurement' }).click()
    expect(onSave).toHaveBeenCalledWith('White', 'after calibration')
  })

  it('falls back to a default label and empty note', () => {
    const onSave = vi.fn()
    render(<HistoryTable entries={[]} onSave={onSave} onClear={() => {}} />)
    screen.getByRole('button', { name: 'Save measurement' }).click()
    expect(onSave).toHaveBeenCalledWith('Measurement 1', '')
  })

})

describe('HistoryTable export', () => {
  it('disables Export CSV when there are no entries', () => {
    render(<HistoryTable entries={[]} onSave={() => {}} onClear={() => {}} />)
    expect(screen.getByRole('button', { name: 'Export CSV' })).toBeDisabled()
  })

  it('exports the entries on click', () => {
    const exportCsv = mockExport()
    render(<HistoryTable entries={entries} onSave={() => {}} onClear={() => {}} />)
    fireEvent.click(screen.getByRole('button', { name: 'Export CSV' }))
    expect(exportCsv).toHaveBeenCalledWith(entries)
  })

  it('shows the saved file name', () => {
    mockExport({ lastPath: '/Users/x/Downloads/PCA-100-history-1.csv' })
    render(<HistoryTable entries={entries} onSave={() => {}} onClear={() => {}} />)
    expect(screen.getByText(/PCA-100-history-1\.csv/)).toBeInTheDocument()
  })

  it('shows the export error text', () => {
    mockExport({ error: 'boom' })
    render(<HistoryTable entries={entries} onSave={() => {}} onClear={() => {}} />)
    expect(screen.getByRole('alert')).toHaveTextContent('boom')
  })
})
