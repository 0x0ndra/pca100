import { Wifi } from 'lucide-react'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Switch } from '@/components/ui/switch'
import { useRemoteAccess, type RemoteAccess } from '@/hooks/use-remote-access'
import { useI18n } from '@/lib/lang'

function ConnectDetails({ state }: { state: RemoteAccess }) {
  const { t } = useI18n()

  if (!state.enabled) {
    return <p className="text-sm text-muted-foreground">{t.remote.empty}</p>
  }

  if (state.urls.length === 0) {
    return <p className="text-sm text-muted-foreground">{t.remote.noUrls}</p>
  }

  return (
    <div className="flex flex-col gap-3">
      <div>
        <p className="text-xs font-medium text-muted-foreground">{t.remote.urlsTitle}</p>
        <ul className="mt-1 flex flex-col gap-0.5">
          {state.urls.map((url) => (
            <li key={url} className="text-sm text-foreground">
              {url}
            </li>
          ))}
        </ul>
      </div>
      {state.qr && <img src={state.qr} alt={t.remote.qrAlt} className="h-40 w-40 self-start" />}
    </div>
  )
}

export function RemoteAccessDialog() {
  const { t } = useI18n()
  const { state, setEnabled, refresh } = useRemoteAccess()

  return (
    <Dialog onOpenChange={(open) => open && refresh()}>
      <DialogTrigger
        render={<Button variant="ghost" size="icon" aria-label={t.remote.trigger} />}
      >
        <Wifi />
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t.remote.title}</DialogTitle>
          <DialogDescription>{t.remote.description}</DialogDescription>
        </DialogHeader>
        <label className="flex items-center gap-2.5 text-sm">
          <Switch
            checked={state?.enabled ?? false}
            onCheckedChange={(enabled) => setEnabled(enabled)}
          />
          <span>{t.remote.toggle}</span>
        </label>
        {state && <ConnectDetails state={state} />}
        <p className="text-xs text-destructive">{t.remote.caution}</p>
      </DialogContent>
    </Dialog>
  )
}
