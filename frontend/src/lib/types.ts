export type Measurement = {
  luminance_ftl: number
  luminance_cdm2: number
  x: number
  y: number
  cct_k: number
  duv: number
  integration_ms: number
  stable: boolean
  stability: 'acquiring' | 'stable' | 'fluctuating'
  variation_pct: number
  saturated: boolean
  timestamp: string
  wavelengths?: number[]
  spectrum?: number[]
}

export type Status = {
  connected: boolean
  serial: string
  scanning: boolean
  averaging: boolean
  integration_ms: number
  dark_active: boolean
  calibration_present: boolean
  error?: string | null
}
