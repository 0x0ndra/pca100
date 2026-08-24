import spectralLocus from './spectral-locus.json'

const DOMAIN_X = 0.8
const DOMAIN_Y = 0.9

export function xyToSvg(x: number, y: number, size: number): { cx: number; cy: number } {
  return {
    cx: (x / DOMAIN_X) * size,
    cy: size - (y / DOMAIN_Y) * size,
  }
}

export function locusPath(size: number): string {
  const pairs = spectralLocus as [number, number][]
  const commands = pairs.map(([x, y], index) => {
    const { cx, cy } = xyToSvg(x, y, size)
    return `${index === 0 ? 'M' : 'L'} ${cx},${cy}`
  })
  return `${commands.join(' ')} Z`
}
