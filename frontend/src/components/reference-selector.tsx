import {
  REFERENCE_KEYS,
  referenceShort,
  type ReferenceControl,
  type ReferenceKey,
} from '@/lib/dci-targets'
import { useI18n } from '@/lib/lang'
import { cn } from '@/lib/utils'

function Segment({
  active,
  label,
  onSelect,
}: {
  active: boolean
  label: string
  onSelect: () => void
}) {
  return (
    <button
      type="button"
      aria-pressed={active}
      onClick={onSelect}
      className={cn(
        'rounded-md px-2.5 py-1 text-xs font-medium transition-colors outline-none focus-visible:ring-2 focus-visible:ring-ring',
        active
          ? 'bg-background text-foreground shadow-sm'
          : 'text-muted-foreground hover:text-foreground',
      )}
    >
      {label}
    </button>
  )
}

function NumberField({
  label,
  value,
  step,
  onChange,
}: {
  label: string
  value: number
  step: number
  onChange: (value: number) => void
}) {
  return (
    <label className="flex flex-col gap-1 text-[0.65rem] font-medium uppercase tracking-widest text-muted-foreground">
      {label}
      <input
        type="number"
        step={step}
        value={value}
        onChange={(e) => {
          const next = e.target.valueAsNumber
          if (Number.isFinite(next)) onChange(next)
        }}
        className="w-20 rounded-md border border-input bg-background px-2 py-1 font-mono text-xs tabular-nums text-foreground outline-none focus-visible:ring-2 focus-visible:ring-ring"
      />
    </label>
  )
}

function CustomInputs({ control }: { control: ReferenceControl }) {
  const { t } = useI18n()
  const { custom, onCustomChange } = control
  return (
    <div className="flex flex-wrap gap-3">
      <NumberField label={t.reference.whiteX} value={custom.whiteX} step={0.001} onChange={(x) => onCustomChange({ whiteX: x })} />
      <NumberField label={t.reference.whiteY} value={custom.whiteY} step={0.001} onChange={(y) => onCustomChange({ whiteY: y })} />
      <NumberField
        label={t.reference.lumFtl}
        value={custom.luminanceFtl}
        step={0.1}
        onChange={(l) => onCustomChange({ luminanceFtl: l })}
      />
    </div>
  )
}

export function ReferenceSelector({ control }: { control: ReferenceControl }) {
  const { t } = useI18n()
  const { key, onSelect, rec709Lum, onRec709LumChange } = control
  return (
    <div className="space-y-3">
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs font-medium text-muted-foreground">{t.reference.label}:</span>
        <div className="inline-flex gap-0.5 rounded-lg border border-border bg-muted/40 p-0.5">
          {REFERENCE_KEYS.map((k: ReferenceKey) => (
            <Segment
              key={k}
              active={k === key}
              label={referenceShort(k, t.reference.custom)}
              onSelect={() => onSelect(k)}
            />
          ))}
        </div>
      </div>
      {key === 'custom' && <CustomInputs control={control} />}
      {key === 'rec709' && (
        <div className="flex flex-wrap gap-3">
          <NumberField label={t.reference.lumFtl} value={rec709Lum} step={0.1} onChange={onRec709LumChange} />
        </div>
      )}
    </div>
  )
}
