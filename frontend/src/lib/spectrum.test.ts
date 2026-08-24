import { describe, expect, it } from 'vitest'
import { PLOT_H, fillPath, linePath, toX, visiblePoints } from './spectrum'

describe('visiblePoints', () => {
  it('drops samples outside the plotted 380..780 nm band', () => {
    const points = visiblePoints([339.68, 380, 580, 780, 1028.98], [1, 2, 3, 4, 5])
    expect(points.map((p) => p.value)).toEqual([2, 3, 4])
  })

  it('ignores a spectrum longer than the wavelength grid', () => {
    expect(visiblePoints([500, 600], [1, 2, 3, 4])).toHaveLength(2)
  })

  it('returns nothing when the grid misses the band entirely', () => {
    expect(visiblePoints([900, 1000], [7, 8])).toEqual([])
  })

  it('maps band edges to the plot edges', () => {
    const points = visiblePoints([380, 780], [1, 1])
    expect(points[0].x).toBe(toX(380))
    expect(points[1].x).toBe(toX(780))
  })
})

describe('linePath', () => {
  it('scales to the in-band peak, ignoring near-IR output', () => {
    // A xenon/laser projector puts strong output above 780 nm. Normalising
    // against it used to flatten the visible curve to a sliver.
    const grid = [400, 550, 700, 900]
    const withoutNearIr = linePath(visiblePoints(grid, [10, 100, 10, 0]))
    const withNearIr = linePath(visiblePoints(grid, [10, 100, 10, 5000]))
    expect(withoutNearIr).toBe(withNearIr)
    expect(withoutNearIr).toContain('0.00') // in-band peak reaches the top
  })

  it('flattens an all-zero spectrum to the baseline', () => {
    expect(linePath(visiblePoints([400, 500], [0, 0]))).toBe(
      `M ${toX(400).toFixed(2)},${PLOT_H}.00 L ${toX(500).toFixed(2)},${PLOT_H}.00`,
    )
  })
})

describe('fillPath', () => {
  it('closes under the plotted points only, not the full plot width', () => {
    const points = visiblePoints([339.68, 580, 1028.98], [1, 2, 3])
    expect(fillPath(points)).toBe('M 200.00,0.00 L 200.00,160 L 200.00,160 Z')
  })
})
