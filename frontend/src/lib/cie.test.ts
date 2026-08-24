import { describe, expect, it } from 'vitest'
import { locusPath, xyToSvg } from './cie'
import locus from './spectral-locus.json'

describe('xyToSvg', () => {
  it('maps the domain origin to bottom-left', () => {
    expect(xyToSvg(0, 0, 300)).toEqual({ cx: 0, cy: 300 })
  })

  it('maps the domain corner (0.8, 0.9) to top-right', () => {
    expect(xyToSvg(0.8, 0.9, 300)).toEqual({ cx: 300, cy: 0 })
  })

  it('scales linearly with size', () => {
    expect(xyToSvg(0.4, 0.45, 200)).toEqual({ cx: 100, cy: 100 })
  })
})

describe('locusPath', () => {
  const path = locusPath(300)

  it('starts with M and ends with Z', () => {
    expect(path.startsWith('M')).toBe(true)
    expect(path.endsWith('Z')).toBe(true)
  })

  it('contains as many M/L segments as there are JSON pairs', () => {
    const body = path.slice(0, -2)
    const segments = body.split(/\s+(?=[ML])/)
    expect(segments).toHaveLength((locus as number[][]).length)
  })
})
