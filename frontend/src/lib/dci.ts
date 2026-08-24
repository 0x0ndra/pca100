import { formatChroma } from './format'
import type { ReferenceTarget } from './dci-targets'

export type TargetKey = 'white' | 'red' | 'green' | 'blue' | 'cyan' | 'magenta' | 'yellow'

export type DciStatus = 'ok' | 'marginal' | 'out'
export type ColorStatus = DciStatus | 'info'

type AxisTol = { plus: number; minus: number }
type PrimaryKey = 'red' | 'green' | 'blue'
type SecondaryKey = 'cyan' | 'magenta' | 'yellow'

type DciTarget = {
  key: TargetKey
  x: number
  y: number
  informative: boolean
  tol?: { x: AxisTol; y: AxisTol }
}

const sym = (v: number): AxisTol => ({ plus: v, minus: v })

// SMPTE RP 431-2 derived per-role boxes; applied regardless of the reference's coords.
const PRIMARY_TOL: Record<PrimaryKey, { x: AxisTol; y: AxisTol }> = {
  red: { x: sym(0.01), y: sym(0.01) },
  green: { x: sym(0.02), y: sym(0.02) },
  blue: { x: { plus: 0.01, minus: 0.03 }, y: { plus: 0.02, minus: 0.04 } },
}

export const WHITE_UV_TOLERANCE = 0.006

// SMPTE RP 431-2 white luminance: 14 fL nominal, +/- LUMINANCE_TOL_FTL in
// tolerance, out beyond LUMINANCE_MARGINAL_FTL.
export const LUMINANCE_TOL_FTL = 2
const LUMINANCE_MARGINAL_FTL = 3

function primaryTarget(key: PrimaryKey, xy: { x: number; y: number }): DciTarget {
  return { key, x: xy.x, y: xy.y, informative: false, tol: PRIMARY_TOL[key] }
}

function secondaryTarget(key: SecondaryKey, xy: { x: number; y: number }): DciTarget {
  return { key, x: xy.x, y: xy.y, informative: true }
}

function buildTargets(ref: ReferenceTarget): DciTarget[] {
  const targets: DciTarget[] = [
    { key: 'white', x: ref.white.x, y: ref.white.y, informative: false },
    primaryTarget('red', ref.primaries.red),
    primaryTarget('green', ref.primaries.green),
    primaryTarget('blue', ref.primaries.blue),
  ]
  const s = ref.secondaries
  if (s) {
    targets.push(
      secondaryTarget('cyan', s.cyan),
      secondaryTarget('magenta', s.magenta),
      secondaryTarget('yellow', s.yellow),
    )
  }
  return targets
}

export type DciResult = {
  target: { key: TargetKey; informative: boolean }
  color: { status: ColorStatus; deltaLabel: string; ratio: number }
  luminance?: { status: DciStatus; deltaFtl: number; targetFtl: number }
}

export function xyToUv(x: number, y: number): { up: number; vp: number } {
  const denom = -2 * x + 12 * y + 3
  return { up: (4 * x) / denom, vp: (9 * y) / denom }
}

function deltaUv(x: number, y: number, target: DciTarget): number {
  const a = xyToUv(x, y)
  const b = xyToUv(target.x, target.y)
  return Math.hypot(a.up - b.up, a.vp - b.vp)
}

const fmt3 = formatChroma

function statusFromRatio(ratio: number): DciStatus {
  if (ratio <= 1) return 'ok'
  if (ratio <= 1.5) return 'marginal'
  return 'out'
}

function nearestTarget(
  x: number,
  y: number,
  targets: DciTarget[],
): { target: DciTarget; delta: number } {
  let best = targets[0]
  let bestDelta = Infinity
  for (const target of targets) {
    const delta = deltaUv(x, y, target)
    if (delta < bestDelta) {
      best = target
      bestDelta = delta
    }
  }
  return { target: best, delta: bestDelta }
}

function axisRatio(value: number, target: number, tol: AxisTol): number {
  const dev = value - target
  return Math.abs(dev) / (dev >= 0 ? tol.plus : tol.minus)
}

function whiteColor(delta: number): DciResult['color'] {
  const ratio = delta / WHITE_UV_TOLERANCE
  return { status: statusFromRatio(ratio), deltaLabel: `Δu'v' ${fmt3(delta)}`, ratio }
}

function infoColor(delta: number): DciResult['color'] {
  return { status: 'info', deltaLabel: `Δu'v' ${fmt3(delta)}`, ratio: delta / WHITE_UV_TOLERANCE }
}

function primaryColor(x: number, y: number, target: DciTarget): DciResult['color'] {
  const tol = target.tol!
  const rx = axisRatio(x, target.x, tol.x)
  const ry = axisRatio(y, target.y, tol.y)
  const worst = Math.max(rx, ry)
  const xDrives = rx >= ry
  const worstDev = Math.abs(xDrives ? x - target.x : y - target.y)
  const deltaLabel = `${xDrives ? 'Δx' : 'Δy'} ${fmt3(worstDev)}`
  return { status: statusFromRatio(worst), deltaLabel, ratio: worst }
}

function evalColor(x: number, y: number, delta: number, target: DciTarget): DciResult['color'] {
  if (target.key === 'white') return whiteColor(delta)
  if (target.informative) return infoColor(delta)
  return primaryColor(x, y, target)
}

function evalLuminance(luminanceFtl: number, targetFtl: number): DciResult['luminance'] {
  const deltaFtl = luminanceFtl - targetFtl
  const abs = Math.abs(deltaFtl)
  const status: DciStatus =
    abs <= LUMINANCE_TOL_FTL ? 'ok' : abs <= LUMINANCE_MARGINAL_FTL ? 'marginal' : 'out'
  return { status, deltaFtl, targetFtl }
}

export function evaluateDci(
  x: number,
  y: number,
  luminanceFtl: number,
  reference: ReferenceTarget,
): DciResult {
  const targets = buildTargets(reference)
  const { target, delta } = nearestTarget(x, y, targets)
  const luminance =
    target.key === 'white' ? evalLuminance(luminanceFtl, reference.luminanceFtl) : undefined
  return {
    target: { key: target.key, informative: target.informative },
    color: evalColor(x, y, delta, target),
    luminance,
  }
}
