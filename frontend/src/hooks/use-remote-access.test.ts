import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import * as api from '@/lib/api'
import type { RemoteAccess } from '@/lib/api'
import { useRemoteAccess } from './use-remote-access'

vi.mock('@/lib/api', () => ({
  fetchRemoteAccess: vi.fn(),
  setRemoteAccess: vi.fn(),
}))

function makeState(overrides: Partial<RemoteAccess> = {}): RemoteAccess {
  return { enabled: false, urls: [], qr: null, ...overrides }
}

afterEach(() => {
  vi.resetAllMocks()
})

describe('useRemoteAccess', () => {
  it('fetches on mount and exposes the result', async () => {
    vi.mocked(api.fetchRemoteAccess).mockResolvedValue(makeState())
    const { result } = renderHook(() => useRemoteAccess())

    await waitFor(() => expect(result.current.state).toEqual(makeState()))
    expect(result.current.error).toBe(false)
  })

  it('refresh() re-fetches on demand', async () => {
    vi.mocked(api.fetchRemoteAccess).mockResolvedValue(makeState())
    const { result } = renderHook(() => useRemoteAccess())
    await waitFor(() => expect(result.current.state).not.toBeNull())
    expect(api.fetchRemoteAccess).toHaveBeenCalledTimes(1)

    act(() => result.current.refresh())

    await waitFor(() => expect(api.fetchRemoteAccess).toHaveBeenCalledTimes(2))
  })

  it('setEnabled() calls setRemoteAccess and updates state', async () => {
    vi.mocked(api.fetchRemoteAccess).mockResolvedValue(makeState())
    vi.mocked(api.setRemoteAccess).mockResolvedValue(makeState({ enabled: true }))
    const { result } = renderHook(() => useRemoteAccess())
    await waitFor(() => expect(result.current.state).not.toBeNull())

    act(() => result.current.setEnabled(true))

    await waitFor(() => expect(result.current.state?.enabled).toBe(true))
    expect(api.setRemoteAccess).toHaveBeenCalledWith(true)
  })

  it('sets an error instead of throwing when the fetch fails', async () => {
    vi.mocked(api.fetchRemoteAccess).mockRejectedValue(new Error('network down'))
    const { result } = renderHook(() => useRemoteAccess())

    await waitFor(() => expect(result.current.error).toBe(true))
    expect(result.current.state).toBeNull()
  })
})
