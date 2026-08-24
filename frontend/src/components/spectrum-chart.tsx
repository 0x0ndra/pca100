import { useMemo } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  PLOT_H,
  PLOT_W,
  fillPath,
  linePath,
  toOffset,
  toX,
  visiblePoints,
  type SpectrumPoint,
} from '@/lib/spectrum'
import { useI18n } from '@/lib/lang'
import type { Measurement } from '@/lib/types'

const TICKS = [380, 480, 580, 680, 780]

// Visible-spectrum stops: wavelength (nm) mapped left->right across the 380..780 plot range.
const SPECTRAL_STOPS: [number, string][] = [
  [380, '#6a00a8'],
  [440, '#2000ff'],
  [470, '#0090ff'],
  [490, '#00d5c8'],
  [510, '#00e000'],
  [560, '#b4e000'],
  [580, '#ffd000'],
  [610, '#ff7000'],
  [645, '#ff1a1a'],
  [700, '#a80000'],
  [780, '#400000'],
]

function SpectrumGradient() {
  return (
    <linearGradient id="spectrum-fill" x1="0" y1="0" x2="1" y2="0">
      {SPECTRAL_STOPS.map(([nm, color]) => (
        <stop key={nm} offset={toOffset(nm)} stopColor={color} />
      ))}
    </linearGradient>
  )
}

function EmptyState() {
  const { t } = useI18n()
  return (
    <div className="flex h-40 items-center justify-center text-sm text-muted-foreground">
      {t.spectrum.empty}
    </div>
  )
}

function Plot({ points }: { points: SpectrumPoint[] }) {
  const { t } = useI18n()
  return (
    <svg
      viewBox={`-14 -6 ${PLOT_W + 28} ${PLOT_H + 28}`}
      className="w-full text-muted-foreground"
      role="img"
      aria-label={t.spectrum.aria}
    >
      <defs>
        <SpectrumGradient />
      </defs>
      <path
        data-testid="spectrum-fill"
        d={fillPath(points)}
        fill="url(#spectrum-fill)"
        fillOpacity={0.55}
      />
      <path
        data-testid="spectrum-line"
        d={linePath(points)}
        fill="none"
        stroke="var(--foreground)"
        strokeOpacity={0.9}
        strokeWidth={2}
        strokeLinejoin="round"
      />
      <line x1={0} y1={PLOT_H} x2={PLOT_W} y2={PLOT_H} stroke="currentColor" strokeOpacity={0.3} />
      {TICKS.map((nm) => (
        <text
          key={nm}
          x={toX(nm)}
          y={PLOT_H + 16}
          fill="currentColor"
          fontSize={10}
          textAnchor="middle"
        >
          {nm}
        </text>
      ))}
    </svg>
  )
}

export function SpectrumChart({ measurement }: { measurement: Measurement | null }) {
  const { t } = useI18n()
  const wavelengths = measurement?.wavelengths
  const spectrum = measurement?.spectrum
  const points = useMemo(
    () => (wavelengths && spectrum ? visiblePoints(wavelengths, spectrum) : []),
    [wavelengths, spectrum],
  )
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>{t.spectrum.title}</CardTitle>
        {measurement && (
          <span className="text-xs text-muted-foreground">
            {t.spectrum.integration}: {measurement.integration_ms} ms
          </span>
        )}
      </CardHeader>
      <CardContent>{points.length > 0 ? <Plot points={points} /> : <EmptyState />}</CardContent>
    </Card>
  )
}
