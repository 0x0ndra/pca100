import { describe, expect, it } from 'vitest'
import { evaluateDci, xyToUv } from './dci'
import { DEFAULT_CUSTOM, resolveReference } from './dci-targets'

const DCI = resolveReference('dci', DEFAULT_CUSTOM, 14)
const P3_D65 = resolveReference('p3-d65', DEFAULT_CUSTOM, 14)
const REC709 = resolveReference('rec709', DEFAULT_CUSTOM, 14)

describe('xyToUv', () => {
  it('matches the CIE 1976 conversion for D65', () => {
    const { up, vp } = xyToUv(0.3127, 0.329)
    expect(up).toBeCloseTo(0.1978, 4)
    expect(vp).toBeCloseTo(0.4683, 4)
  })
})

describe('evaluateDci reference switching', () => {
  it('DCI white on-target is ok with luminance present', () => {
    const r = evaluateDci(0.314, 0.351, 14.0, DCI)
    expect(r.target.key).toBe('white')
    expect(r.color.status).toBe('ok')
    expect(r.luminance?.status).toBe('ok')
    expect(r.luminance?.targetFtl).toBe(14)
  })

  it('D65 white passes under the P3-D65 reference', () => {
    const r = evaluateDci(0.3127, 0.329, 14.0, P3_D65)
    expect(r.target.key).toBe('white')
    expect(r.color.status).toBe('ok')
  })

  it('D65 white is out under the DCI reference', () => {
    const r = evaluateDci(0.3127, 0.329, 14.0, DCI)
    expect(r.target.key).toBe('white')
    expect(r.color.status).toBe('out')
    expect(r.color.ratio).toBeGreaterThan(1.5)
  })

  it('Rec.709 reference detects Rec.709 red as nearest and evaluates its box', () => {
    const r = evaluateDci(0.64, 0.33, 14.0, REC709)
    expect(r.target.key).toBe('red')
    expect(r.color.status).toBe('ok')
    expect(r.luminance).toBeUndefined()
  })

  it('a custom reference evaluates against its own white and luminance', () => {
    const custom = resolveReference('custom', { whiteX: 0.3, whiteY: 0.34, luminanceFtl: 12 }, 14)
    const r = evaluateDci(0.3, 0.34, 12.0, custom)
    expect(r.target.key).toBe('white')
    expect(r.color.status).toBe('ok')
    expect(r.luminance?.status).toBe('ok')
    expect(r.luminance?.targetFtl).toBe(12)
  })
})

describe('evaluateDci luminance bands', () => {
  it('is ok within +/- 2 fL of the reference target', () => {
    expect(evaluateDci(0.314, 0.351, 15.9, DCI).luminance?.status).toBe('ok')
  })

  it('is marginal between 2 and 3 fL off target', () => {
    const r = evaluateDci(0.314, 0.351, 16.5, DCI)
    expect(r.luminance?.status).toBe('marginal')
    expect(r.luminance?.deltaFtl).toBeCloseTo(2.5, 6)
  })

  it('is out beyond 3 fL off target', () => {
    expect(evaluateDci(0.314, 0.351, 18.0, DCI).luminance?.status).toBe('out')
  })
})

describe('evaluateDci primaries and secondaries', () => {
  it('P3 red just outside the box is out', () => {
    const r = evaluateDci(0.7, 0.32, 14.0, DCI)
    expect(r.target.key).toBe('red')
    expect(r.color.status).toBe('out')
    expect(r.color.ratio).toBeCloseTo(2, 4)
    expect(r.color.deltaLabel).toBe('Δx 0.020')
  })

  it('marks a CMY point as informative with info status', () => {
    const r = evaluateDci(0.2047, 0.3603, 14.0, DCI)
    expect(r.target.key).toBe('cyan')
    expect(r.target.informative).toBe(true)
    expect(r.color.status).toBe('info')
    expect(r.color.deltaLabel).toContain("Δu'v'")
  })

  it('applies the asymmetric blue box on the minus side', () => {
    const r = evaluateDci(0.15, 0.02, 14.0, DCI)
    expect(r.target.key).toBe('blue')
    expect(r.color.status).toBe('ok')
  })
})
