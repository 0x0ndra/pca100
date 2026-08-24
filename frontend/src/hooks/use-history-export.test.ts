import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as api from '@/lib/api'
import type { HistoryEntry } from './use-history'
import { useHistoryExport } from './use-history-export'

vi.mock('@/lib/api', () => ({ exportHistory: vi.fn() }))

const entries = [{ id: 1, label: 'White', note: '' }] as unknown as HistoryEntry[]

afterEach(() => vi.resetAllMocks())

describe('useHistoryExport', () => {
  it('posts the entries and exposes the saved path', async () => {
    vi.mocked(api.exportHistory).mockResolvedValue({ path: '/Users/x/Downloads/a.csv' })
    const { result } = renderHook(() => useHistoryExport())

    act(() => result.current.exportCsv(entries))

    await waitFor(() => expect(result.current.lastPath).toBe('/Users/x/Downloads/a.csv'))
    expect(api.exportHistory).toHaveBeenCalledWith(entries)
    expect(result.current.error).toBeNull()
    expect(result.current.pending).toBe(false)
  })

  it('exposes the error text when the export fails', async () => {
    vi.mocked(api.exportHistory).mockRejectedValue(new Error('boom'))
    const { result } = renderHook(() => useHistoryExport())

    act(() => result.current.exportCsv(entries))

    await waitFor(() => expect(result.current.error).toBe('boom'))
    expect(result.current.lastPath).toBeNull()
  })

  it('clears a previous error on the next success', async () => {
    vi.mocked(api.exportHistory).mockRejectedValueOnce(new Error('boom'))
    vi.mocked(api.exportHistory).mockResolvedValueOnce({ path: '/a.csv' })
    const { result } = renderHook(() => useHistoryExport())

    act(() => result.current.exportCsv(entries))
    await waitFor(() => expect(result.current.error).toBe('boom'))
    act(() => result.current.exportCsv(entries))
    await waitFor(() => expect(result.current.lastPath).toBe('/a.csv'))
    expect(result.current.error).toBeNull()
  })
})
