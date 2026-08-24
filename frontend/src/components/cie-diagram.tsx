import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { locusPath, xyToSvg } from '@/lib/cie'
import { referenceShort, type ReferenceTarget } from '@/lib/dci-targets'
import { useI18n } from '@/lib/lang'
import type { Measurement } from '@/lib/types'

export const CIE_SIZE = 300
const CLIP_ID = 'cie-locus-clip'
const INK = '#ffffff'
const SHADOW = '#000000'

function gamutPoints(reference: ReferenceTarget): string {
  const { red, green, blue } = reference.primaries
  return [red, green, blue]
    .map((p) => {
      const { cx, cy } = xyToSvg(p.x, p.y, CIE_SIZE)
      return `${cx},${cy}`
    })
    .join(' ')
}

function ReferenceOverlay({ reference }: { reference: ReferenceTarget }) {
  const { t } = useI18n()
  const { cx, cy } = xyToSvg(reference.white.x, reference.white.y, CIE_SIZE)
  const points = gamutPoints(reference)
  return (
    <g style={{ filter: `drop-shadow(0 0 1px ${SHADOW})` }}>
      <polygon
        points={points}
        fill="none"
        stroke={SHADOW}
        strokeOpacity={0.35}
        strokeWidth={3}
        strokeDasharray="4 3"
      />
      <polygon
        data-testid="gamut-triangle"
        points={points}
        fill={INK}
        fillOpacity={0.04}
        stroke={INK}
        strokeWidth={1.5}
        strokeDasharray="4 3"
      />
      <line x1={cx - 6} y1={cy} x2={cx + 6} y2={cy} stroke={INK} strokeWidth={1.5} />
      <line x1={cx} y1={cy - 6} x2={cx} y2={cy + 6} stroke={INK} strokeWidth={1.5} />
      <text
        data-testid="gamut-label"
        x={cx + 9}
        y={cy - 5}
        fill={INK}
        fontSize={9}
        stroke={SHADOW}
        strokeWidth={0.4}
      >
        {referenceShort(reference.key, t.reference.custom)}
      </text>
    </g>
  )
}

function MeasuredPoint({ measurement }: { measurement: Measurement }) {
  const { cx, cy } = xyToSvg(measurement.x, measurement.y, CIE_SIZE)
  return (
    <g>
      <circle cx={cx} cy={cy} r={6} fill="none" stroke={SHADOW} strokeOpacity={0.4} strokeWidth={4} />
      <circle cx={cx} cy={cy} r={6} fill="none" stroke={INK} strokeWidth={2} />
      <circle data-testid="measured-point" cx={cx} cy={cy} r={2.5} fill={SHADOW} />
    </g>
  )
}

export function CieDiagram({
  measurement,
  reference,
  showReference,
}: {
  measurement: Measurement | null
  reference: ReferenceTarget
  showReference: boolean
}) {
  const { t } = useI18n()
  return (
    <Card>
      <CardHeader>
        <CardTitle>{t.cie.title}</CardTitle>
      </CardHeader>
      <CardContent>
        <svg
          viewBox={`-8 -8 ${CIE_SIZE + 16} ${CIE_SIZE + 16}`}
          className="w-full text-muted-foreground"
          role="img"
          aria-label={t.cie.aria}
        >
          <defs>
            <clipPath id={CLIP_ID}>
              <path d={locusPath(CIE_SIZE)} />
            </clipPath>
          </defs>
          <image
            data-testid="cie-fill"
            href="/cie-chromaticity.png"
            x={0}
            y={0}
            width={CIE_SIZE}
            height={CIE_SIZE}
            preserveAspectRatio="none"
            clipPath={`url(#${CLIP_ID})`}
          />
          <path
            d={locusPath(CIE_SIZE)}
            fill="none"
            stroke="currentColor"
            strokeOpacity={0.6}
            strokeWidth={1.5}
          />
          {showReference && <ReferenceOverlay reference={reference} />}
          {measurement && <MeasuredPoint measurement={measurement} />}
        </svg>
      </CardContent>
    </Card>
  )
}
