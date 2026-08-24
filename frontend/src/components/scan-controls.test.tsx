import { render, screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { Status } from '@/lib/types'
import { ScanControls } from './scan-controls'

const base: Status = {
  connected: true,
  serial: 'PCA-0302',
  scanning: true,
  averaging: true,
  integration_ms: 100,
  dark_active: false,
  calibration_present: true,
}

function renderControls(status: Status, onDark = vi.fn(), onClearDark = vi.fn()) {
  render(
    <ScanControls
      status={status}
      wsConnected
      onStart={() => {}}
      onStop={() => {}}
      onDark={onDark}
      onClearDark={onClearDark}
      onSetAveraging={() => {}}
    />,
  )
  return { onDark, onClearDark }
}

describe('ScanControls dark handling', () => {
  it('captures a runtime dark when none is active', () => {
    const { onDark, onClearDark } = renderControls(base)
    screen.getByRole('button', { name: 'Capture dark' }).click()
    expect(onDark).toHaveBeenCalledOnce()
    expect(onClearDark).not.toHaveBeenCalled()
  })

  it('clears the runtime dark once one is active', () => {
    const { onDark, onClearDark } = renderControls({ ...base, dark_active: true })
    screen.getByRole('button', { name: 'Clear dark' }).click()
    expect(onClearDark).toHaveBeenCalledOnce()
    expect(onDark).not.toHaveBeenCalled()
  })

  it('warns that an active runtime dark replaces the calibrated model', () => {
    renderControls({ ...base, dark_active: true })
    expect(screen.getByText(/Runtime dark active/)).toBeInTheDocument()
  })

  it('says nothing about dark when none is active', () => {
    renderControls(base)
    expect(screen.queryByText(/Runtime dark active/)).toBeNull()
  })
})
