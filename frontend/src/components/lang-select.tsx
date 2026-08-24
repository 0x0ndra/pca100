import { useI18n, type Lang } from '@/lib/lang'
import { STRINGS } from '@/lib/strings'

export function LangSelect() {
  const { lang, setLang } = useI18n()
  return (
    <select
      aria-label="Language"
      value={lang}
      onChange={(e) => setLang(e.target.value as Lang)}
      className="rounded-lg border border-border bg-secondary/40 px-2.5 py-1.5 text-xs text-muted-foreground transition-colors hover:border-primary/40 hover:text-primary"
    >
      {Object.entries(STRINGS).map(([code, strings]) => (
        <option key={code} value={code}>
          {strings.label}
        </option>
      ))}
    </select>
  )
}
