import { Badge } from '@/components/ui/badge'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { ReferenceSelector } from '@/components/reference-selector'
import type { ReferenceControl } from '@/lib/dci-targets'
import { LUMINANCE_TOL_FTL, type ColorStatus, type DciResult } from '@/lib/dci'
import { formatFtl, formatSignedFtl } from '@/lib/format'
import { useI18n } from '@/lib/lang'
import type { Strings } from '@/lib/strings'

const STATUS_STYLE: Record<ColorStatus, { badge: string; marker: string }> = {
  ok: {
    badge: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
    marker: 'bg-emerald-400',
  },
  marginal: {
    badge: 'border-amber-500/40 bg-amber-500/10 text-amber-400',
    marker: 'bg-amber-400',
  },
  out: {
    badge: 'border-destructive/40 bg-destructive/15 text-destructive',
    marker: 'bg-destructive',
  },
  info: {
    badge: 'border-border bg-muted text-muted-foreground',
    marker: 'bg-muted-foreground',
  },
}

function statusLabel(status: ColorStatus, t: Strings): string {
  if (status === 'ok') return t.dci.pass
  if (status === 'marginal') return t.dci.marginal
  if (status === 'out') return t.dci.out
  return t.dci.informative
}

// Bar spans ratio 0..2: OK zone ends at 1 (50%), marginal at 1.5 (75%), out beyond.
function ToleranceBar({ ratio, status }: { ratio: number; status: ColorStatus }) {
  const pos = Math.min(Math.max(ratio, 0), 2) / 2
  const zoned = status !== 'info'
  return (
    <div className="relative h-2 w-full overflow-hidden rounded-full bg-muted" aria-hidden>
      {zoned && (
        <>
          <div className="absolute inset-y-0 left-0 w-1/2 bg-emerald-500/15" />
          <div className="absolute inset-y-0 left-1/2 w-1/4 bg-amber-500/15" />
          <div className="absolute inset-y-0 left-3/4 w-1/4 bg-destructive/15" />
        </>
      )}
      <div
        className={`absolute top-0 h-full w-[3px] -translate-x-1/2 rounded-full ring-2 ring-card ${STATUS_STYLE[status].marker}`}
        style={{ left: `${pos * 100}%` }}
      />
    </div>
  )
}

function MetricRow({
  label,
  target,
  status,
  ratio,
  delta,
}: {
  label: string
  target?: string
  status: ColorStatus
  ratio: number
  delta: string
}) {
  const { t } = useI18n()
  return (
    <div className="space-y-1.5">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-sm font-medium">{label}</span>
        {target && <span className="text-xs text-muted-foreground">{target}</span>}
      </div>
      <div className="flex items-center gap-3">
        <ToleranceBar ratio={ratio} status={status} />
        <Badge variant="outline" className={`shrink-0 ${STATUS_STYLE[status].badge}`}>
          {statusLabel(status, t)}
        </Badge>
        <span className="w-24 shrink-0 text-right font-mono text-xs tabular-nums text-muted-foreground">
          {delta}
        </span>
      </div>
    </div>
  )
}

function Metrics({ result }: { result: DciResult }) {
  const { t } = useI18n()
  return (
    <div className="space-y-4 border-t border-border/60 pt-4">
      <MetricRow
        label={t.dci.color}
        target={result.target.informative ? t.dci.informativeLower : undefined}
        status={result.color.status}
        ratio={result.color.ratio}
        delta={result.color.deltaLabel}
      />
      {result.luminance && (
        <MetricRow
          label={t.measurement.luminance}
          target={`${formatFtl(result.luminance.targetFtl)} fL`}
          status={result.luminance.status}
          ratio={Math.abs(result.luminance.deltaFtl) / LUMINANCE_TOL_FTL}
          delta={formatSignedFtl(result.luminance.deltaFtl)}
        />
      )}
    </div>
  )
}

export function DciCompliance({
  result,
  control,
}: {
  result: DciResult | null
  control: ReferenceControl
}) {
  const { t } = useI18n()
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>{t.dci.title}</CardTitle>
        {result && (
          <Badge variant="secondary">
            {t.dci.target}: {t.targets[result.target.key]}
          </Badge>
        )}
      </CardHeader>
      <CardContent className="space-y-4">
        <ReferenceSelector control={control} />
        {result ? (
          <Metrics result={result} />
        ) : (
          <p className="text-sm text-muted-foreground">{t.dci.aim}</p>
        )}
      </CardContent>
    </Card>
  )
}
