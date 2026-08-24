import { useCallback, useState } from 'react'
import { exportHistory } from '@/lib/api'
import type { HistoryEntry } from './use-history'

export function useHistoryExport() {
  const [pending, setPending] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [lastPath, setLastPath] = useState<string | null>(null)

  const exportCsv = useCallback((entries: HistoryEntry[]) => {
    setPending(true)
    setError(null)
    exportHistory(entries)
      .then(({ path }) => setLastPath(path))
      .catch((e: unknown) => {
        setLastPath(null)
        setError(e instanceof Error ? e.message : String(e))
      })
      .finally(() => setPending(false))
  }, [])

  return { exportCsv, pending, error, lastPath }
}
