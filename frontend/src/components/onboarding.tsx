type OnboardingProps = {
  onReveal: () => void
  onReload: () => void
  showError?: boolean
}

const CAL_PATH = '~/Library/Application Support/PCA-100/calibration'
const FILES = ['dark.bin', 'lamp.bin', 'reference.bin', 'colormeter.ini']

export function Onboarding({ onReveal, onReload, showError = false }: OnboardingProps) {
  return (
    <div className="mx-auto max-w-xl space-y-6 rounded-2xl border border-border bg-card p-8">
      <div className="space-y-2">
        <h1 className="font-display text-2xl font-semibold">Calibration needed</h1>
        <p className="text-sm text-muted-foreground">
          PCA-100 needs the calibration files of your specific instrument. They are the same
          files the original USL software uses, copy them from that installation.
        </p>
      </div>
      <div className="space-y-2 text-sm">
        <p>Copy these files into:</p>
        <code className="block rounded-lg bg-secondary/50 px-3 py-2 text-xs">{CAL_PATH}</code>
        <ul className="list-inside list-disc text-muted-foreground">
          {FILES.map((f) => (
            <li key={f}>{f}</li>
          ))}
        </ul>
      </div>
      <div className="flex gap-3">
        <button
          onClick={onReveal}
          className="rounded-lg border border-border px-4 py-2 text-sm transition-colors hover:border-primary/40 hover:text-primary"
        >
          Open folder
        </button>
        <button
          onClick={onReload}
          className="rounded-lg bg-primary px-4 py-2 text-sm font-medium text-primary-foreground transition-opacity hover:opacity-90"
        >
          Load calibration
        </button>
      </div>
      {showError && (
        <p className="text-sm text-destructive">
          Calibration files not found or failed to load. Check the folder and try again.
        </p>
      )}
    </div>
  )
}
