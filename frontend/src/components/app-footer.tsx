import { Code2, Contact, Globe } from 'lucide-react'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { useI18n } from '@/lib/lang'

type DevLink = { href: string; label: string; icon: typeof Globe }

const LINKS: DevLink[] = [
  { href: 'https://github.com/0x0ndra', label: 'GitHub', icon: Code2 },
  { href: 'https://ondra-vlasek.cz', label: 'Web', icon: Globe },
  { href: 'https://www.linkedin.com/in/ondravlasek/', label: 'LinkedIn', icon: Contact },
]

function DevLinkRow({ href, label, icon: Icon }: DevLink) {
  return (
    <a
      href={href}
      target="_blank"
      rel="noopener noreferrer"
      className="flex items-center gap-2.5 rounded-lg border border-border bg-secondary/40 px-3 py-2 text-sm text-foreground transition-colors hover:border-primary/40 hover:text-primary"
    >
      <Icon className="size-4 text-muted-foreground" aria-hidden="true" />
      {label}
    </a>
  )
}

function DeveloperDialog() {
  const { t } = useI18n()
  return (
    <Dialog>
      <DialogTrigger className="text-muted-foreground underline-offset-4 transition-colors hover:text-primary hover:underline">
        0x0ndra
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>{t.footer.developer}</DialogTitle>
          <DialogDescription>{t.footer.tagline}</DialogDescription>
        </DialogHeader>
        <div className="space-y-1">
          <p className="font-display text-lg font-semibold leading-tight">Ondra Vlášek</p>
          <p className="text-sm text-muted-foreground">0x0ndra</p>
        </div>
        <div className="grid gap-2 sm:grid-cols-3">
          {LINKS.map((link) => (
            <DevLinkRow key={link.href} {...link} />
          ))}
        </div>
        <p className="text-xs text-muted-foreground">{t.footer.appDesc}</p>
      </DialogContent>
    </Dialog>
  )
}

export function AppFooter() {
  return (
    <footer className="flex items-center justify-end gap-2 border-t border-border/60 pt-4 text-xs text-muted-foreground">
      <a
        href="https://xctech.cz"
        target="_blank"
        rel="noopener noreferrer"
        className="underline-offset-4 transition-colors hover:text-primary hover:underline"
      >
        xctech.cz
      </a>
      <span aria-hidden="true" className="text-border">|</span>
      <DeveloperDialog />
    </footer>
  )
}
