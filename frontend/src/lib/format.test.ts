import { afterEach, describe, expect, it } from 'vitest'
import {
  formatChroma,
  formatCct,
  formatLuminance,
  formatSignedFtl,
  formatTimestamp,
  setFormatLocale,
} from './format'
import { STRINGS } from './strings'

afterEach(() => setFormatLocale(STRINGS.en.locale))

describe('formatLuminance', () => {
  it('uses three decimals below 10', () => {
    expect(formatLuminance(5.4321)).toBe('5.432')
  })

  it('uses three decimals at or above 10', () => {
    expect(formatLuminance(12.3456)).toBe('12.346')
  })

  it('pads to three decimals', () => {
    expect(formatLuminance(10)).toBe('10.000')
  })

  it('rounds half-up values to three decimals', () => {
    expect(formatLuminance(16.6054)).toBe('16.605')
  })
})

describe('formatChroma', () => {
  it('formats with exactly 3 decimals', () => {
    expect(formatChroma(0.3127)).toBe('0.313')
  })

  it('pads short values to 3 decimals', () => {
    expect(formatChroma(0.3)).toBe('0.300')
  })
})

describe('formatCct', () => {
  it('formats as an integer with grouping and a K suffix', () => {
    expect(formatCct(4740)).toBe(`${(4740).toLocaleString('en-US')} K`)
  })
})

describe('formatSignedFtl', () => {
  it('signs both directions', () => {
    expect(formatSignedFtl(2.5)).toBe('+2.5 fL')
    expect(formatSignedFtl(-2.5)).toBe('-2.5 fL')
  })
})

describe('formatTimestamp', () => {
  const iso = '2026-07-24T13:42:03Z'

  it('formats an ISO timestamp in the active locale', () => {
    expect(formatTimestamp(iso)).toBe(new Date(iso).toLocaleString('en-US'))
    expect(formatTimestamp(iso)).toContain('2026')
  })

  it('returns a dash for an invalid timestamp', () => {
    expect(formatTimestamp('not-a-date')).toBe('—')
  })
})

describe('setFormatLocale', () => {
  it('switches decimal separators and grouping to cs-CZ', () => {
    setFormatLocale(STRINGS.cs.locale)
    expect(formatChroma(0.3127)).toBe('0,313')
    expect(formatCct(4740)).toBe(`${(4740).toLocaleString('cs-CZ')} K`)
  })
})
