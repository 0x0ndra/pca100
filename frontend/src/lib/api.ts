import type { Measurement, Status } from './types'

async function requestJson<T>(path: string, init?: RequestInit): Promise<T> {
  const res = await fetch(path, init)
  if (!res.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${path} failed with ${res.status}`)
  }
  return (await res.json()) as T
}

async function requestOk(path: string, init?: RequestInit): Promise<void> {
  const res = await fetch(path, init)
  if (!res.ok) {
    throw new Error(`${init?.method ?? 'GET'} ${path} failed with ${res.status}`)
  }
}

export function fetchStatus(): Promise<Status> {
  return requestJson<Status>('/api/status')
}

export function startScan(): Promise<Status> {
  return requestJson<Status>('/api/scan/start', { method: 'POST' })
}

export function stopScan(): Promise<Status> {
  return requestJson<Status>('/api/scan/stop', { method: 'POST' })
}

export function setAveraging(enabled: boolean): Promise<Status> {
  return requestJson<Status>('/api/averaging', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  })
}

export function captureDark(): Promise<void> {
  return requestOk('/api/dark', { method: 'POST' })
}

export function clearDark(): Promise<void> {
  return requestOk('/api/dark', { method: 'DELETE' })
}

export function reloadCalibration(): Promise<{ calibration_present: boolean }> {
  return requestJson<{ calibration_present: boolean }>('/api/calibration/reload', { method: 'POST' })
}

export function revealCalibration(): Promise<void> {
  return requestOk('/api/calibration/reveal', { method: 'POST' })
}

export type DownloadState = {
  state: 'idle' | 'downloading' | 'downloaded' | 'error'
  error: string | null
  path: string | null
}

export type UpdateInfo = {
  current: string
  latest: string | null
  available: boolean
  release_url: string | null
  error: string | null
  download: DownloadState
}

export function fetchUpdate(): Promise<UpdateInfo> {
  return requestJson<UpdateInfo>('/api/update')
}

export function startUpdateDownload(): Promise<UpdateInfo> {
  return requestJson<UpdateInfo>('/api/update/download', { method: 'POST' })
}

export type RemoteAccess = {
  enabled: boolean
  urls: string[]
  qr: string | null
}

export function fetchRemoteAccess(): Promise<RemoteAccess> {
  return requestJson<RemoteAccess>('/api/remote-access')
}

export function setRemoteAccess(enabled: boolean): Promise<RemoteAccess> {
  return requestJson<RemoteAccess>('/api/remote-access', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ enabled }),
  })
}

export type HistoryExportEntry = { label: string; note: string; measurement: Measurement }

export function exportHistory(entries: HistoryExportEntry[]): Promise<{ path: string }> {
  return requestJson<{ path: string }>('/api/history/export', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(entries),
  })
}
