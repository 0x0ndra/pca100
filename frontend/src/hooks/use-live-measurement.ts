import { useEffect, useRef, useState } from 'react'
import type { Measurement } from '@/lib/types'

const RECONNECT_DELAY_MS = 2000

function liveWsUrl(): string {
  const protocol = location.protocol === 'https:' ? 'wss' : 'ws'
  return `${protocol}://${location.host}/api/live`
}

export function useLiveMeasurement(): { measurement: Measurement | null; wsConnected: boolean } {
  const [measurement, setMeasurement] = useState<Measurement | null>(null)
  const [wsConnected, setWsConnected] = useState(false)
  const socketRef = useRef<WebSocket | null>(null)
  const reconnectRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  useEffect(() => {
    let cancelled = false

    function connect(): void {
      const socket = new WebSocket(liveWsUrl())
      socketRef.current = socket

      socket.onopen = () => setWsConnected(true)
      socket.onmessage = (event) => setMeasurement(JSON.parse(event.data) as Measurement)
      socket.onclose = () => {
        setWsConnected(false)
        if (!cancelled) {
          reconnectRef.current = setTimeout(connect, RECONNECT_DELAY_MS)
        }
      }
    }

    connect()

    return () => {
      cancelled = true
      if (reconnectRef.current) clearTimeout(reconnectRef.current)
      socketRef.current?.close()
    }
  }, [])

  return { measurement, wsConnected }
}
