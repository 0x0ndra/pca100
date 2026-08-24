import { Badge } from '@/components/ui/badge'
import { useI18n } from '@/lib/lang'
import type { Strings } from '@/lib/strings'

type DeviceStatusProps = {
  connected: boolean | undefined
  serial: string | undefined
  error?: string | null
}

function statusConfig(connected: boolean | undefined, t: Strings) {
  if (connected === true) {
    return {
      label: t.device.connected,
      badgeClassName: 'border-emerald-500/40 bg-emerald-500/10 text-emerald-400',
      dotClassName: 'bg-emerald-400',
    }
  }
  if (connected === false) {
    return {
      label: t.device.disconnected,
      badgeClassName: 'border-destructive/40 bg-destructive/10 text-destructive',
      dotClassName: 'bg-destructive',
    }
  }
  return {
    label: t.device.probing,
    badgeClassName: 'border-border text-muted-foreground',
    dotClassName: 'bg-muted-foreground',
  }
}

export function DeviceStatus({ connected, serial, error }: DeviceStatusProps) {
  const { t } = useI18n()
  const { label, badgeClassName, dotClassName } = statusConfig(connected, t)

  return (
    <Badge variant="outline" className={badgeClassName} title={error ?? undefined}>
      <span className={`h-1.5 w-1.5 shrink-0 rounded-full ${dotClassName}`} aria-hidden="true" />
      <span>{label}</span>
      {connected === true && serial ? (
        <span className="text-muted-foreground">· {serial}</span>
      ) : null}
    </Badge>
  )
}
