import { Loader2 } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useUpdate, type UpdateInfo } from '@/hooks/use-update'
import { useI18n } from '@/lib/lang'

function DownloadAction({ info, onDownload }: { info: UpdateInfo; onDownload: () => void }) {
  const { t } = useI18n()
  const { state, error } = info.download

  if (state === 'downloaded') {
    return <p className="text-sm text-foreground">{t.update.downloaded}</p>
  }

  if (state === 'error') {
    return <p className="text-sm text-destructive">{error ?? t.update.error}</p>
  }

  return (
    <Button onClick={onDownload} disabled={state === 'downloading'}>
      {state === 'downloading' && <Loader2 className="animate-spin" aria-hidden="true" />}
      {state === 'downloading' ? t.update.downloading : t.update.download}
    </Button>
  )
}

export function UpdateBanner() {
  const { t } = useI18n()
  const { info, download } = useUpdate()

  if (!info?.available) {
    return null
  }

  return (
    <Dialog>
      <DialogTrigger
        render={<Badge variant="secondary" className="cursor-pointer" />}
      >
        {t.update.badge} {info.latest}
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t.update.title}</DialogTitle>
          <DialogDescription>{t.update.description}</DialogDescription>
        </DialogHeader>
        {info.release_url && (
          <a
            href={info.release_url}
            target="_blank"
            rel="noopener noreferrer"
            className="text-sm text-primary underline-offset-4 hover:underline"
          >
            {t.update.releaseNotes}
          </a>
        )}
        <DownloadAction info={info} onDownload={download} />
      </DialogContent>
    </Dialog>
  )
}
