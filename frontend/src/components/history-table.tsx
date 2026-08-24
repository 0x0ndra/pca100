import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { formatChroma, formatCct, formatLuminance, formatTimestamp } from '@/lib/format'
import type { HistoryEntry } from '@/hooks/use-history'
import { useHistoryExport } from '@/hooks/use-history-export'
import { useI18n } from '@/lib/lang'

export type { HistoryEntry }

const COLUMNS = 8

function EntryRow({ entry }: { entry: HistoryEntry }) {
  const m = entry.measurement
  return (
    <TableRow>
      <TableCell className="font-medium">{entry.label}</TableCell>
      <TableCell className="max-w-48 truncate text-muted-foreground" title={entry.note || undefined}>
        {entry.note || '—'}
      </TableCell>
      <TableCell className="text-right font-mono tabular-nums">{formatLuminance(m.luminance_ftl)}</TableCell>
      <TableCell className="text-right font-mono tabular-nums">{formatLuminance(m.luminance_cdm2)}</TableCell>
      <TableCell className="text-right font-mono tabular-nums">{formatChroma(m.x)}</TableCell>
      <TableCell className="text-right font-mono tabular-nums">{formatChroma(m.y)}</TableCell>
      <TableCell className="text-right font-mono tabular-nums">{formatCct(m.cct_k)}</TableCell>
      <TableCell className="text-right whitespace-nowrap text-muted-foreground tabular-nums">
        {formatTimestamp(m.timestamp)}
      </TableCell>
    </TableRow>
  )
}

const INPUT_CLASS =
  'h-8 rounded-lg border border-border bg-background px-2.5 text-sm outline-none focus-visible:ring-3 focus-visible:ring-ring/50'

function SaveRow({
  onSave,
  count,
}: {
  onSave: (label: string, note: string) => void
  count: number
}) {
  const { t } = useI18n()
  const [label, setLabel] = useState('')
  const [note, setNote] = useState('')
  function save() {
    onSave(label.trim() || `${t.history.defaultLabel} ${count + 1}`, note.trim())
    setLabel('')
    setNote('')
  }
  return (
    <div className="flex flex-wrap gap-2">
      <input
        value={label}
        onChange={(e) => setLabel(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && save()}
        placeholder={t.history.placeholder}
        className={`${INPUT_CLASS} w-40 flex-none sm:w-48`}
      />
      <input
        value={note}
        onChange={(e) => setNote(e.target.value)}
        onKeyDown={(e) => e.key === 'Enter' && save()}
        placeholder={t.history.notePlaceholder}
        className={`${INPUT_CLASS} min-w-32 flex-1`}
      />
      <Button onClick={save}>{t.history.save}</Button>
    </div>
  )
}

type ExportState = ReturnType<typeof useHistoryExport>

function ExportStatus({ error, lastPath }: Pick<ExportState, 'error' | 'lastPath'>) {
  const { t } = useI18n()
  const fileName = lastPath?.split('/').pop()
  return (
    <>
      {fileName && (
        <p role="status" className="text-sm text-muted-foreground">
          {t.history.exported}: {fileName}
        </p>
      )}
      {error && (
        <p role="alert" className="text-sm text-destructive">
          {t.history.exportError}: {error}
        </p>
      )}
    </>
  )
}

function HeaderActions({
  entries,
  onClear,
  exportCsv,
  pending,
}: { entries: HistoryEntry[]; onClear: () => void } & Pick<ExportState, 'exportCsv' | 'pending'>) {
  const { t } = useI18n()
  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="sm"
        disabled={entries.length === 0 || pending}
        onClick={() => exportCsv(entries)}
      >
        {t.history.export}
      </Button>
      {entries.length > 0 && (
        <Button variant="ghost" size="sm" onClick={onClear}>
          {t.history.clear}
        </Button>
      )}
    </div>
  )
}

export function HistoryTable({
  entries,
  onSave,
  onClear,
}: {
  entries: HistoryEntry[]
  onSave: (label: string, note: string) => void
  onClear: () => void
}) {
  const { t } = useI18n()
  const { exportCsv, pending, error, lastPath } = useHistoryExport()
  return (
    <Card>
      <CardHeader className="flex-row items-center justify-between">
        <CardTitle>{t.history.title}</CardTitle>
        <HeaderActions entries={entries} onClear={onClear} exportCsv={exportCsv} pending={pending} />
      </CardHeader>
      <CardContent className="space-y-3">
        <ExportStatus error={error} lastPath={lastPath} />
        <SaveRow onSave={onSave} count={entries.length} />
        <Table>
          <TableHeader>
            <TableRow>
              <TableHead>{t.history.name}</TableHead>
              <TableHead>{t.history.note}</TableHead>
              <TableHead className="text-right">fL</TableHead>
              <TableHead className="text-right">cd/m²</TableHead>
              <TableHead className="text-right">x</TableHead>
              <TableHead className="text-right">y</TableHead>
              <TableHead className="text-right">CCT</TableHead>
              <TableHead className="text-right">{t.history.time}</TableHead>
            </TableRow>
          </TableHeader>
          <TableBody>
            {entries.length === 0 ? (
              <TableRow>
                <TableCell colSpan={COLUMNS} className="text-center text-muted-foreground">
                  {t.history.empty}
                </TableCell>
              </TableRow>
            ) : (
              entries.map((entry) => <EntryRow key={entry.id} entry={entry} />)
            )}
          </TableBody>
        </Table>
      </CardContent>
    </Card>
  )
}
