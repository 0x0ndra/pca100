export const PLOT_W = 400
export const PLOT_H = 160
export const MIN_NM = 380
export const MAX_NM = 780

export type SpectrumPoint = { x: number; value: number }

export function toOffset(nm: number): number {
  return (nm - MIN_NM) / (MAX_NM - MIN_NM)
}

export function toX(nm: number): number {
  return toOffset(nm) * PLOT_W
}

// The spectrometer returns its full ~340..1030 nm grid. Everything outside the
// plotted band has to be dropped before scaling, or near-IR lamp output (strong
// on xenon and laser projectors) sets the peak and squashes the visible curve.
export function visiblePoints(wavelengths: number[], spectrum: number[]): SpectrumPoint[] {
  const points: SpectrumPoint[] = []
  const count = Math.min(wavelengths.length, spectrum.length)
  for (let i = 0; i < count; i += 1) {
    const nm = wavelengths[i]
    if (nm >= MIN_NM && nm <= MAX_NM) points.push({ x: toX(nm), value: spectrum[i] })
  }
  return points
}

export function linePath(points: SpectrumPoint[]): string {
  let peak = 0
  for (const point of points) if (point.value > peak) peak = point.value
  const scale = peak > 0 ? PLOT_H / peak : 0
  return points
    .map(
      (point, i) =>
        `${i === 0 ? 'M' : 'L'} ${point.x.toFixed(2)},${(PLOT_H - point.value * scale).toFixed(2)}`,
    )
    .join(' ')
}

export function fillPath(points: SpectrumPoint[]): string {
  const first = points[0].x.toFixed(2)
  const last = points[points.length - 1].x.toFixed(2)
  return `${linePath(points)} L ${last},${PLOT_H} L ${first},${PLOT_H} Z`
}
