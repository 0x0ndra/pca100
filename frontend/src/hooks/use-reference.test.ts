import { beforeEach, describe, expect, it } from 'vitest'
import { loadReferenceState, saveReferenceState, type ReferenceState } from './use-reference'

describe('reference persistence', () => {
  beforeEach(() => {
    localStorage.clear()
  })

  it('defaults to the DCI reference when nothing is stored', () => {
    expect(loadReferenceState().key).toBe('dci')
  })

  it('round-trips the selected key and custom values', () => {
    const state: ReferenceState = {
      key: 'custom',
      custom: { whiteX: 0.3, whiteY: 0.34, luminanceFtl: 12 },
      rec709Lum: 13.5,
    }
    saveReferenceState(state)
    const loaded = loadReferenceState()
    expect(loaded.key).toBe('custom')
    expect(loaded.custom).toEqual(state.custom)
    expect(loaded.rec709Lum).toBe(13.5)
  })

  it('falls back to defaults for a corrupt payload', () => {
    localStorage.setItem('pca-reference', '{not json')
    expect(loadReferenceState().key).toBe('dci')
  })
})
