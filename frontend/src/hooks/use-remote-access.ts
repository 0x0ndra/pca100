import { useCallback, useEffect, useState } from 'react'
import { fetchRemoteAccess, setRemoteAccess, type RemoteAccess } from '@/lib/api'

export type { RemoteAccess } from '@/lib/api'

export function useRemoteAccess() {
  const [state, setState] = useState<RemoteAccess | null>(null)
  const [error, setError] = useState(false)

  const refresh = useCallback(() => {
    fetchRemoteAccess()
      .then((next) => {
        setState(next)
        setError(false)
      })
      .catch(() => setError(true))
  }, [])

  useEffect(() => {
    refresh()
  }, [refresh])

  const setEnabled = useCallback((enabled: boolean) => {
    setRemoteAccess(enabled)
      .then((next) => {
        setState(next)
        setError(false)
      })
      .catch(() => setError(true))
  }, [])

  return { state, error, setEnabled, refresh }
}
