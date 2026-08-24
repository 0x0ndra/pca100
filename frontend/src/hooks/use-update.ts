import { useCallback, useEffect, useState } from 'react'
import { fetchUpdate, startUpdateDownload, type UpdateInfo } from '@/lib/api'

export type { UpdateInfo } from '@/lib/api'

const POLL_INTERVAL_MS = 60_000

export function useUpdate() {
  const [info, setInfo] = useState<UpdateInfo | null>(null)
  const [error, setError] = useState(false)

  const refresh = useCallback(() => {
    fetchUpdate()
      .then((next) => {
        setInfo(next)
        setError(false)
      })
      .catch(() => setError(true))
  }, [])

  useEffect(() => {
    refresh()
    const id = setInterval(refresh, POLL_INTERVAL_MS)
    return () => clearInterval(id)
  }, [refresh])

  const download = useCallback(() => {
    startUpdateDownload()
      .then((next) => {
        setInfo(next)
        setError(false)
      })
      .catch(() => setError(true))
  }, [])

  return { info, error, download }
}
