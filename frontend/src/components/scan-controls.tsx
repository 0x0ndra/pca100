import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Switch } from '@/components/ui/switch'
import { useI18n } from '@/lib/lang'
import type { Status } from '@/lib/types'

function ConnectionBadge({ wsConnected }: { wsConnected: boolean }) {
  const { t } = useI18n()
  return (
    <Badge
      variant="outline"
      className={
        wsConnected
          ? 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400'
          : 'border-destructive/40 bg-destructive/10 text-destructive'
      }
    >
      {wsConnected ? t.controls.live : t.controls.offline}
    </Badge>
  )
}

function ScanButton({
  scanning,
  onStart,
  onStop,
}: {
  scanning: boolean
  onStart: () => void
  onStop: () => void
}) {
  const { t } = useI18n()
  return (
    <Button
      className="flex-1"
      variant={scanning ? 'destructive' : 'default'}
      onClick={scanning ? onStop : onStart}
    >
      {scanning ? t.controls.stopScan : t.controls.startScan}
    </Button>
  )
}

function DarkButton({
  darkActive,
  onDark,
  onClearDark,
}: {
  darkActive: boolean
  onDark: () => void
  onClearDark: () => void
}) {
  const { t } = useI18n()
  return (
    <Button variant="outline" onClick={darkActive ? onClearDark : onDark}>
      {darkActive ? t.controls.clearDark : t.controls.measureDark}
    </Button>
  )
}

function AveragingRow({
  averaging,
  onSetAveraging,
}: {
  averaging: boolean
  onSetAveraging: (enabled: boolean) => void
}) {
  const { t } = useI18n()
  return (
    <div className="flex items-center justify-between">
      <div className="space-y-0.5">
        <div className="text-sm font-medium">{t.controls.averaging}</div>
        <div className="text-xs text-muted-foreground">{t.controls.averagingDetail}</div>
      </div>
      <Switch checked={averaging} onCheckedChange={onSetAveraging} aria-label={t.controls.averaging} />
    </div>
  )
}

function DeviceLine({ status }: { status: Status }) {
  const { t } = useI18n()
  return (
    <div className="text-xs text-muted-foreground">
      {t.controls.integration}: {status.integration_ms} ms · {t.controls.serial}: {status.serial || '—'}
    </div>
  )
}

type ScanControlsProps = {
  status: Status | undefined
  wsConnected: boolean
  onStart: () => void
  onStop: () => void
  onDark: () => void
  onClearDark: () => void
  onSetAveraging: (enabled: boolean) => void
}

export function ScanControls({
  status,
  wsConnected,
  onStart,
  onStop,
  onDark,
  onClearDark,
  onSetAveraging,
}: ScanControlsProps) {
  const { t } = useI18n()
  const darkActive = status?.dark_active ?? false
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>{t.controls.title}</CardTitle>
        <ConnectionBadge wsConnected={wsConnected} />
      </CardHeader>
      <CardContent className="space-y-3">
        <div className="flex gap-2">
          <ScanButton
            scanning={status?.scanning ?? false}
            onStart={onStart}
            onStop={onStop}
          />
          <DarkButton darkActive={darkActive} onDark={onDark} onClearDark={onClearDark} />
        </div>
        {darkActive && (
          <p className="text-xs text-amber-400">{t.controls.darkActive}</p>
        )}
        <AveragingRow averaging={status?.averaging ?? false} onSetAveraging={onSetAveraging} />
        {status && <DeviceLine status={status} />}
      </CardContent>
    </Card>
  )
}
