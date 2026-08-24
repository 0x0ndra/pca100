import { beforeEach, describe, expect, it } from 'vitest'
import type { Measurement } from '@/lib/types'
import { loadHistory, saveHistory, type HistoryEntry } from './use-history'

const measurement: Measurement = {
  luminance_ftl: 14,
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
  timestamp: '2026-07-27T09:00:00Z',
}

describe('loadHistory/saveHistory', () => {
  beforeEach(() => localStorage.clear())

  it('starts empty', () => {
    expect(loadHistory()).toEqual([])
  })

  it('round-trips entries with notes', () => {
    const entries: HistoryEntry[] = [
      { id: 2, label: 'White', note: 'after lamp swap', measurement },
      { id: 1, label: 'Green', note: '', measurement },
    ]
    saveHistory(entries)
    expect(loadHistory()).toEqual(entries)
  })

  it('fills a missing note on entries saved before the note field existed', () => {
    localStorage.setItem('pca-history', JSON.stringify([{ id: 1, label: 'White', measurement }]))
    expect(loadHistory()[0].note).toBe('')
  })

  it('drops malformed entries and survives corrupt storage', () => {
    localStorage.setItem(
      'pca-history',
      JSON.stringify([{ id: 1, label: 'ok', measurement }, { label: 'no id' }, 42]),
    )
    expect(loadHistory()).toHaveLength(1)
    localStorage.setItem('pca-history', 'not json')
    expect(loadHistory()).toEqual([])
  })
})
