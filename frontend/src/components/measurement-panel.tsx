import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import type { DciStatus } from '@/lib/dci'
import { formatChroma, formatCct, formatLuminance, formatVariation } from '@/lib/format'
import { useI18n } from '@/lib/lang'
import type { Strings } from '@/lib/strings'
import type { Measurement } from '@/lib/types'

type Unit = 'ftl' | 'cdm2'

const UNIT_LABEL: Record<Unit, string> = { ftl: 'ftL', cdm2: 'cd/m²' }

const LUM_COLOR: Record<DciStatus, string> = {
  ok: 'text-emerald-400',
  marginal: 'text-amber-400',
  out: 'text-destructive',
}

function LuminanceLegend({ t }: { t: Strings }) {
  const legend: { dot: string; label: string }[] = [
    { dot: 'bg-emerald-400', label: t.measurement.inTolerance },
    { dot: 'bg-amber-400', label: t.measurement.marginal },
    { dot: 'bg-destructive', label: t.measurement.out },
  ]
  return (
    <div className="flex flex-wrap items-center gap-x-3 gap-y-1 text-[0.65rem] text-muted-foreground">
      {legend.map((item) => (
        <span key={item.label} className="flex items-center gap-1.5">
          <span className={`size-1.5 rounded-full ${item.dot}`} aria-hidden />
          {item.label}
        </span>
      ))}
    </div>
  )
}

const STABILITY_CLASS: Record<Measurement['stability'], string> = {
  acquiring: 'border-muted-foreground/30 bg-muted text-muted-foreground',
  stable: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
  fluctuating: 'border-amber-500/40 bg-amber-500/10 text-amber-400',
}

function stabilityLabel(stability: Measurement['stability'], t: Strings): string {
  if (stability === 'stable') return t.measurement.stable
  if (stability === 'fluctuating') return t.measurement.fluctuating
  return t.measurement.acquiring
}

function chroma(value: number | undefined): string {
  return value === undefined ? '—' : formatChroma(value)
}

function StatusBadges({ measurement }: { measurement: Measurement | null }) {
  const { t } = useI18n()
  if (!measurement) {
    return <Badge variant="outline">{t.measurement.waiting}</Badge>
  }
  return (
    <div className="flex items-center gap-1.5">
      {measurement.saturated && <Badge variant="destructive">{t.measurement.saturation}</Badge>}
      <Badge variant="outline" className={STABILITY_CLASS[measurement.stability]}>
        {stabilityLabel(measurement.stability, t)}
      </Badge>
      {measurement.stability !== 'acquiring' && (
        <span className="text-xs tabular-nums text-muted-foreground">
          ±{formatVariation(measurement.variation_pct)} %
        </span>
      )}
    </div>
  )
}

function Reading({ label, value }: { label: string; value: string }) {
  return (
    <div className="space-y-0.5">
      <div className="text-[0.65rem] font-medium uppercase tracking-widest text-muted-foreground">
        {label}
      </div>
      <div className="font-display text-2xl font-semibold tabular-nums tracking-tight">{value}</div>
    </div>
  )
}

function LuminanceBlock({
  measurement,
  unit,
  onToggleUnit,
  luminanceStatus,
}: MeasurementPanelProps) {
  const { t } = useI18n()
  const lum = measurement
    ? formatLuminance(unit === 'ftl' ? measurement.luminance_ftl : measurement.luminance_cdm2)
    : '—'
  const lumColor = luminanceStatus ? LUM_COLOR[luminanceStatus] : 'text-primary'
  return (
    <div className="space-y-1.5">
      <div className="text-[0.65rem] font-medium uppercase tracking-widest text-muted-foreground">
        {t.measurement.luminance}
      </div>
      <div className="flex items-baseline gap-3">
        <span
          data-status={luminanceStatus ?? 'none'}
          className={`font-display text-5xl font-bold tabular-nums tracking-tight ${lumColor}`}
        >
          {lum}
        </span>
        <Button
          variant="outline"
          size="sm"
          aria-label={t.measurement.toggleUnit}
          onClick={onToggleUnit}
        >
          {UNIT_LABEL[unit]}
        </Button>
      </div>
      <LuminanceLegend t={t} />
    </div>
  )
}

type MeasurementPanelProps = {
  measurement: Measurement | null
  unit: Unit
  onToggleUnit: () => void
  luminanceStatus?: DciStatus
}

export function MeasurementPanel(props: MeasurementPanelProps) {
  const { t } = useI18n()
  const { measurement } = props
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>{t.measurement.title}</CardTitle>
        <StatusBadges measurement={measurement} />
      </CardHeader>
      <CardContent className="space-y-5">
        <LuminanceBlock {...props} />
        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Reading label="x" value={chroma(measurement?.x)} />
          <Reading label="y" value={chroma(measurement?.y)} />
          <Reading
            label={t.measurement.cct}
            value={measurement ? formatCct(measurement.cct_k) : '—'}
          />
          <Reading label="Δuv" value={chroma(measurement?.duv)} />
        </div>
      </CardContent>
    </Card>
  )
}
