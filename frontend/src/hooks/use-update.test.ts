import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as api from '@/lib/api'
import type { UpdateInfo } from '@/lib/api'
import { useUpdate } from './use-update'

vi.mock('@/lib/api', () => ({
  fetchUpdate: vi.fn(),
  startUpdateDownload: vi.fn(),
}))

function makeInfo(overrides: Partial<UpdateInfo> = {}): UpdateInfo {
  return {
    current: '1.0.0',
    latest: '1.1.0',
    available: true,
    release_url: null,
    error: null,
    download: { state: 'idle', error: null, path: null },
    ...overrides,
  }
}

afterEach(() => {
  vi.resetAllMocks()
  vi.useRealTimers()
})

describe('useUpdate', () => {
  it('fetches on mount and exposes the result', async () => {
    vi.mocked(api.fetchUpdate).mockResolvedValue(makeInfo())
    const { result } = renderHook(() => useUpdate())

    await waitFor(() => expect(result.current.info).toEqual(makeInfo()))
    expect(result.current.error).toBe(false)
  })

  it('polls again after 60s', async () => {
    vi.useFakeTimers()
    vi.mocked(api.fetchUpdate).mockResolvedValue(makeInfo())
    renderHook(() => useUpdate())

    await act(async () => {
      await Promise.resolve()
    })
    expect(api.fetchUpdate).toHaveBeenCalledTimes(1)

    await act(async () => {
      vi.advanceTimersByTime(60_000)
      await Promise.resolve()
    })
    expect(api.fetchUpdate).toHaveBeenCalledTimes(2)
  })

  it('sets an error instead of throwing when the fetch fails', async () => {
    vi.mocked(api.fetchUpdate).mockRejectedValue(new Error('network down'))
    const { result } = renderHook(() => useUpdate())

    await waitFor(() => expect(result.current.error).toBe(true))
    expect(result.current.info).toBeNull()
  })

  it('download() calls startUpdateDownload and updates info', async () => {
    vi.mocked(api.fetchUpdate).mockResolvedValue(makeInfo())
    vi.mocked(api.startUpdateDownload).mockResolvedValue(
      makeInfo({ download: { state: 'downloading', error: null, path: null } }),
    )
    const { result } = renderHook(() => useUpdate())
    await waitFor(() => expect(result.current.info).not.toBeNull())

    act(() => result.current.download())

    await waitFor(() => expect(result.current.info?.download.state).toBe('downloading'))
  })
})
