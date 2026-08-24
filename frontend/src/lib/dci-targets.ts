export type ReferenceKey = 'dci' | 'p3-d65' | 'rec709' | 'custom'

export type Xy = { x: number; y: number }

export type ReferenceTarget = {
  key: ReferenceKey
  white: Xy
  luminanceFtl: number
  primaries: { red: Xy; green: Xy; blue: Xy }
  secondaries?: { cyan: Xy; magenta: Xy; yellow: Xy }
}

const P3_PRIMARIES = {
  red: { x: 0.68, y: 0.32 },
  green: { x: 0.265, y: 0.69 },
  blue: { x: 0.15, y: 0.06 },
}

const P3_SECONDARIES = {
  cyan: { x: 0.2047, y: 0.3603 },
  magenta: { x: 0.3424, y: 0.1544 },
  yellow: { x: 0.4247, y: 0.5477 },
}

const DCI_WHITE: Xy = { x: 0.314, y: 0.351 }
const D65_WHITE: Xy = { x: 0.3127, y: 0.329 }
const DEFAULT_LUM_FTL = 14.0

const DCI_REFERENCE: ReferenceTarget = {
  key: 'dci',
  white: DCI_WHITE,
  luminanceFtl: DEFAULT_LUM_FTL,
  primaries: P3_PRIMARIES,
  secondaries: P3_SECONDARIES,
}

const P3_D65_REFERENCE: ReferenceTarget = {
  key: 'p3-d65',
  white: D65_WHITE,
  luminanceFtl: DEFAULT_LUM_FTL,
  primaries: P3_PRIMARIES,
  secondaries: P3_SECONDARIES,
}

const REC709_REFERENCE: ReferenceTarget = {
  key: 'rec709',
  white: D65_WHITE,
  luminanceFtl: DEFAULT_LUM_FTL,
  primaries: {
    red: { x: 0.64, y: 0.33 },
    green: { x: 0.3, y: 0.6 },
    blue: { x: 0.15, y: 0.06 },
  },
}

export type CustomValues = { whiteX: number; whiteY: number; luminanceFtl: number }

export type ReferenceControl = {
  key: ReferenceKey
  reference: ReferenceTarget
  custom: CustomValues
  rec709Lum: number
  onSelect: (key: ReferenceKey) => void
  onCustomChange: (patch: Partial<CustomValues>) => void
  onRec709LumChange: (luminanceFtl: number) => void
}

export const DEFAULT_CUSTOM: CustomValues = { whiteX: 0.3127, whiteY: 0.329, luminanceFtl: 14.0 }

export const REFERENCE_KEYS: ReferenceKey[] = ['dci', 'p3-d65', 'rec709', 'custom']

const REFERENCE_SHORT: Record<Exclude<ReferenceKey, 'custom'>, string> = {
  dci: 'DCI',
  'p3-d65': 'P3-D65',
  rec709: 'Rec.709',
}

export function referenceShort(key: ReferenceKey, customLabel: string): string {
  return key === 'custom' ? customLabel : REFERENCE_SHORT[key]
}

export function buildRec709Reference(luminanceFtl: number): ReferenceTarget {
  return { ...REC709_REFERENCE, luminanceFtl }
}

export function buildCustomReference(v: CustomValues): ReferenceTarget {
  return {
    key: 'custom',
    white: { x: v.whiteX, y: v.whiteY },
    luminanceFtl: v.luminanceFtl,
    primaries: P3_PRIMARIES,
  }
}

export function resolveReference(
  key: ReferenceKey,
  custom: CustomValues,
  rec709Lum: number,
): ReferenceTarget {
  if (key === 'p3-d65') return P3_D65_REFERENCE
  if (key === 'rec709') return buildRec709Reference(rec709Lum)
  if (key === 'custom') return buildCustomReference(custom)
  return DCI_REFERENCE
}
