import { useCallback, useState } from 'react'
import type { Measurement } from '@/lib/types'

export type HistoryEntry = { id: number; label: string; note: string; measurement: Measurement }

const STORAGE_KEY = 'pca-history'

export function loadHistory(): HistoryEntry[] {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return []
    const parsed = JSON.parse(raw) as Partial<HistoryEntry>[]
    return parsed
      .filter((e) => typeof e.id === 'number' && typeof e.label === 'string' && !!e.measurement)
      .map((e) => ({ ...(e as HistoryEntry), note: e.note ?? '' }))
  } catch {
    return []
  }
}

export function saveHistory(entries: HistoryEntry[]): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(entries))
  } catch {
    // storage unavailable; history simply will not persist
  }
}

export function useHistory() {
  const [entries, setEntries] = useState<HistoryEntry[]>(loadHistory)

  const update = useCallback((next: HistoryEntry[]) => {
    setEntries(next)
    saveHistory(next)
  }, [])

  const save = useCallback(
    (label: string, note: string, measurement: Measurement) => {
      const id = entries.reduce((max, e) => Math.max(max, e.id), 0) + 1
      update([{ id, label, note, measurement }, ...entries])
    },
    [entries, update],
  )

  const clear = useCallback(() => update([]), [update])

  return { entries, save, clear }
}
