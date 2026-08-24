import { useMemo, useState, type ReactNode } from 'react'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { AppFooter } from '@/components/app-footer'
import { AppHeader } from '@/components/app-header'
import { CieDiagram } from '@/components/cie-diagram'
import { DciCompliance } from '@/components/dci-compliance'
import { HistoryTable } from '@/components/history-table'
import { MeasurementPanel } from '@/components/measurement-panel'
import { Onboarding } from '@/components/onboarding'
import { ScanControls } from '@/components/scan-controls'
import { SpectrumChart } from '@/components/spectrum-chart'
import { useCalibration } from '@/hooks/use-calibration'
import { useHistory } from '@/hooks/use-history'
import { useLiveMeasurement } from '@/hooks/use-live-measurement'
import { useReference } from '@/hooks/use-reference'
import { useScan } from '@/hooks/use-scan'
import { evaluateDci, type DciResult } from '@/lib/dci'
import { setFormatLocale } from '@/lib/format'
import { LangContext, loadLang, saveLang, type Lang } from '@/lib/lang'
import { STRINGS } from '@/lib/strings'
import type { Measurement } from '@/lib/types'

const queryClient = new QueryClient()

export function LangProvider({ children }: { children: ReactNode }) {
  const [lang, setLangState] = useState<Lang>(() => loadLang())
  setFormatLocale(STRINGS[lang].locale)
  const value = useMemo(
    () => ({
      lang,
      setLang: (next: Lang) => {
        setLangState(next)
        saveLang(next)
      },
    }),
    [lang],
  )
  return <LangContext.Provider value={value}>{children}</LangContext.Provider>
}

type Unit = 'ftl' | 'cdm2'

type OnboardingScreenProps = {
  showReference: boolean
  onToggleReference: (value: boolean) => void
  calibration: ReturnType<typeof useCalibration>
}

function OnboardingScreen({ showReference, onToggleReference, calibration }: OnboardingScreenProps) {
  const { reload } = calibration
  const showError = reload.isError || reload.data?.calibration_present === false
  return (
    <div className="mx-auto max-w-6xl p-4 sm:p-6">
      <AppHeader showReference={showReference} onToggleReference={onToggleReference} />
      <div className="pt-10">
        <Onboarding
          onReveal={() => calibration.reveal.mutate()}
          onReload={() => reload.mutate()}
          showError={showError}
        />
      </div>
    </div>
  )
}

type MeasurementGridProps = {
  measurement: Measurement | null
  unit: Unit
  onToggleUnit: () => void
  dci: DciResult | null
  reference: ReturnType<typeof useReference>
  showReference: boolean
  wsConnected: boolean
  scan: ReturnType<typeof useScan>
}

function MeasurementGrid({
  measurement,
  unit,
  onToggleUnit,
  dci,
  reference,
  showReference,
  wsConnected,
  scan,
}: MeasurementGridProps) {
  const { status, start, stop, dark, clearDark, setAveraging } = scan
  return (
    <div className="grid gap-4 lg:grid-cols-2">
      <div className="space-y-4">
        <MeasurementPanel
          measurement={measurement}
          unit={unit}
          onToggleUnit={onToggleUnit}
          luminanceStatus={dci?.luminance?.status}
        />
        <DciCompliance result={dci} control={reference} />
        <ScanControls
          status={status.data}
          wsConnected={wsConnected}
          onStart={() => start.mutate()}
          onStop={() => stop.mutate()}
          onDark={() => dark.mutate()}
          onClearDark={() => clearDark.mutate()}
          onSetAveraging={(enabled) => setAveraging.mutate(enabled)}
        />
      </div>
      <div className="space-y-4">
        <CieDiagram measurement={measurement} reference={reference.reference} showReference={showReference} />
        <SpectrumChart measurement={measurement} />
      </div>
    </div>
  )
}

function Dashboard() {
  const { measurement, wsConnected } = useLiveMeasurement()
  const scan = useScan()
  const reference = useReference()
  const [unit, setUnit] = useState<Unit>('ftl')
  const [showReference, setShowReference] = useState(true)
  const history = useHistory()
  const calibration = useCalibration()

  if (scan.status.data && scan.status.data.calibration_present === false) {
    return (
      <OnboardingScreen
        showReference={showReference}
        onToggleReference={setShowReference}
        calibration={calibration}
      />
    )
  }

  const dci = measurement
    ? evaluateDci(measurement.x, measurement.y, measurement.luminance_ftl, reference.reference)
    : null

  function save(label: string, note: string) {
    if (measurement) history.save(label, note, measurement)
  }

  return (
    <div className="mx-auto max-w-6xl space-y-4 p-4 sm:p-6">
      <AppHeader
        showReference={showReference}
        onToggleReference={setShowReference}
        deviceConnected={scan.status.data?.connected}
        deviceSerial={scan.status.data?.serial}
        deviceError={scan.status.data?.error}
      />
      <MeasurementGrid
        measurement={measurement}
        unit={unit}
        onToggleUnit={() => setUnit((u) => (u === 'ftl' ? 'cdm2' : 'ftl'))}
        dci={dci}
        reference={reference}
        showReference={showReference}
        wsConnected={wsConnected}
        scan={scan}
      />
      <HistoryTable entries={history.entries} onSave={save} onClear={history.clear} />
      <AppFooter />
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <LangProvider>
        <div className="dark">
          <div className="min-h-svh bg-background text-foreground">
            <Dashboard />
          </div>
        </div>
      </LangProvider>
    </QueryClientProvider>
  )
}

export default App
