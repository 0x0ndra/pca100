import { useCallback, useMemo, useState } from 'react'
import {
  DEFAULT_CUSTOM,
  resolveReference,
  type CustomValues,
  type ReferenceControl,
  type ReferenceKey,
} from '@/lib/dci-targets'

const STORAGE_KEY = 'pca-reference'
const DEFAULT_REC709_LUM = 14.0

export type ReferenceState = {
  key: ReferenceKey
  custom: CustomValues
  rec709Lum: number
}

const DEFAULT_STATE: ReferenceState = {
  key: 'dci',
  custom: DEFAULT_CUSTOM,
  rec709Lum: DEFAULT_REC709_LUM,
}

export function loadReferenceState(): ReferenceState {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    if (!raw) return DEFAULT_STATE
    const parsed = JSON.parse(raw) as Partial<ReferenceState>
    return {
      key: parsed.key ?? DEFAULT_STATE.key,
      custom: { ...DEFAULT_CUSTOM, ...parsed.custom },
      rec709Lum: parsed.rec709Lum ?? DEFAULT_REC709_LUM,
    }
  } catch {
    return DEFAULT_STATE
  }
}

export function saveReferenceState(state: ReferenceState): void {
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(state))
  } catch {
    // storage unavailable; selection simply will not persist
  }
}

export function useReference(): ReferenceControl {
  const [state, setState] = useState<ReferenceState>(loadReferenceState)

  const update = useCallback((next: ReferenceState) => {
    setState(next)
    saveReferenceState(next)
  }, [])

  const onSelect = useCallback(
    (key: ReferenceKey) => update({ ...state, key }),
    [state, update],
  )
  const onCustomChange = useCallback(
    (patch: Partial<CustomValues>) => update({ ...state, custom: { ...state.custom, ...patch } }),
    [state, update],
  )
  const onRec709LumChange = useCallback(
    (rec709Lum: number) => update({ ...state, rec709Lum }),
    [state, update],
  )

  const reference = useMemo(
    () => resolveReference(state.key, state.custom, state.rec709Lum),
    [state.key, state.custom, state.rec709Lum],
  )

  return {
    key: state.key,
    reference,
    custom: state.custom,
    rec709Lum: state.rec709Lum,
    onSelect,
    onCustomChange,
    onRec709LumChange,
  }
}
