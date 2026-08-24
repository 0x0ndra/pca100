import { DeviceStatus } from '@/components/device-status'
import { LangSelect } from '@/components/lang-select'
import { RemoteAccessDialog } from '@/components/remote-access-dialog'
import { Switch } from '@/components/ui/switch'
import { UpdateBanner } from '@/components/update-banner'
import { useI18n } from '@/lib/lang'

type AppHeaderProps = {
  showReference: boolean
  onToggleReference: (value: boolean) => void
  deviceConnected?: boolean
  deviceSerial?: string
  deviceError?: string | null
}

export function AppHeader({
  showReference,
  onToggleReference,
  deviceConnected,
  deviceSerial,
  deviceError,
}: AppHeaderProps) {
  const { t } = useI18n()
  return (
    <header className="flex flex-wrap items-center justify-between gap-4 border-b border-border/60 pb-4">
      <div className="flex items-center gap-4">
        <img src="/xctech-logo-white.png" alt="XC tech" className="h-7 w-auto" />
        <div className="h-8 w-px bg-border" aria-hidden="true" />
        <div>
          <h1 className="font-display text-2xl font-bold leading-none tracking-tight">PCA-100</h1>
          <p className="mt-1 text-sm text-muted-foreground">{t.header.subtitle}</p>
        </div>
      </div>
      <div className="flex flex-wrap items-center gap-4">
        <UpdateBanner />
        <RemoteAccessDialog />
        <DeviceStatus connected={deviceConnected} serial={deviceSerial} error={deviceError} />
        <LangSelect />
        <label className="flex items-center gap-2.5 text-sm">
          <span className="text-muted-foreground">{t.header.referenceInDiagram}</span>
          <Switch checked={showReference} onCheckedChange={onToggleReference} />
        </label>
      </div>
    </header>
  )
}
