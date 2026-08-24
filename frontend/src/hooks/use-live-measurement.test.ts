import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import type { Measurement } from '@/lib/types'
import { useLiveMeasurement } from './use-live-measurement'

class MockWebSocket {
  static instances: MockWebSocket[] = []
  url: string
  onopen: (() => void) | null = null
  onmessage: ((event: { data: string }) => void) | null = null
  onclose: (() => void) | null = null
  close = vi.fn()

  constructor(url: string) {
    this.url = url
    MockWebSocket.instances.push(this)
  }

  triggerOpen(): void {
    this.onopen?.()
  }

  triggerMessage(data: Measurement): void {
    this.onmessage?.({ data: JSON.stringify(data) })
  }

  triggerClose(): void {
    this.onclose?.()
  }
}

const sampleMeasurement: Measurement = {
  luminance_ftl: 10,
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

beforeEach(() => {
  MockWebSocket.instances = []
  vi.stubGlobal('WebSocket', MockWebSocket)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.useRealTimers()
})

describe('useLiveMeasurement', () => {
  it('updates measurement on incoming message', () => {
    const { result } = renderHook(() => useLiveMeasurement())
    const socket = MockWebSocket.instances[0]

    act(() => {
      socket.triggerMessage(sampleMeasurement)
    })

    expect(result.current.measurement).toEqual(sampleMeasurement)
  })

  it('carries wavelengths and spectrum through when the WS frame includes them', () => {
    const { result } = renderHook(() => useLiveMeasurement())
    const socket = MockWebSocket.instances[0]
    const withSpectrum: Measurement = { ...sampleMeasurement, wavelengths: [380, 480, 580], spectrum: [0.1, 0.2, 0.3] }

    act(() => socket.triggerMessage(withSpectrum))

    expect(result.current.measurement?.wavelengths).toEqual([380, 480, 580])
    expect(result.current.measurement?.spectrum).toEqual([0.1, 0.2, 0.3])
  })

  it('flips wsConnected on open and close', () => {
    const { result } = renderHook(() => useLiveMeasurement())
    const socket = MockWebSocket.instances[0]

    expect(result.current.wsConnected).toBe(false)

    act(() => {
      socket.triggerOpen()
    })
    expect(result.current.wsConnected).toBe(true)

    act(() => {
      socket.triggerClose()
    })
    expect(result.current.wsConnected).toBe(false)
  })

  it('reconnects 2s after the socket closes', () => {
    vi.useFakeTimers()
    renderHook(() => useLiveMeasurement())
    expect(MockWebSocket.instances).toHaveLength(1)

    act(() => {
      MockWebSocket.instances[0].triggerClose()
    })

    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(MockWebSocket.instances).toHaveLength(2)
  })

  it('clears the reconnect timer and closes the socket on unmount', () => {
    vi.useFakeTimers()
    const { unmount } = renderHook(() => useLiveMeasurement())
    const socket = MockWebSocket.instances[0]

    act(() => {
      socket.triggerClose()
    })

    unmount()

    act(() => {
      vi.advanceTimersByTime(2000)
    })

    expect(socket.close).toHaveBeenCalledTimes(1)
    expect(MockWebSocket.instances).toHaveLength(1)
  })
})
