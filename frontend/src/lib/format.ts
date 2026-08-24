import { STRINGS } from './strings'

// Module-level so plain formatting helpers stay call-site cheap; the language
// provider sets it during render, before any consumer formats.
let locale: string = STRINGS.en.locale

export function setFormatLocale(next: string): void {
  locale = next
}

export function formatLuminance(value: number): string {
  return value.toLocaleString(locale, { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

export function formatChroma(value: number): string {
  return value.toLocaleString(locale, { minimumFractionDigits: 3, maximumFractionDigits: 3 })
}

export function formatCct(value: number): string {
  return `${Math.round(value).toLocaleString(locale)} K`
}

export function formatFtl(value: number): string {
  return value.toLocaleString(locale, { minimumFractionDigits: 1, maximumFractionDigits: 1 })
}

export function formatSignedFtl(value: number): string {
  return `${value >= 0 ? '+' : '-'}${formatFtl(Math.abs(value))} fL`
}

export function formatVariation(value: number): string {
  return value.toLocaleString(locale, { minimumFractionDigits: 1, maximumFractionDigits: 1 })
}

export function formatTimestamp(iso: string): string {
  const date = new Date(iso)
  return Number.isNaN(date.getTime()) ? '—' : date.toLocaleString(locale)
}
