import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { DeviceStatus } from './device-status'

describe('DeviceStatus', () => {
  it('shows connected label and serial when the spectrometer is attached', () => {
    render(<DeviceStatus connected={true} serial="USB2+F00302" />)
    expect(screen.getByText('Meter connected')).toBeInTheDocument()
    expect(screen.getByText('· USB2+F00302')).toBeInTheDocument()
  })

  it('shows disconnected label in a destructive-styled badge when the device is not attached', () => {
    render(<DeviceStatus connected={false} serial={undefined} />)
    const label = screen.getByText('Meter disconnected')
    expect(label).toBeInTheDocument()
    expect(label.parentElement).toHaveClass('text-destructive')
  })

  it('shows a neutral loading label while the status is unknown', () => {
    render(<DeviceStatus connected={undefined} serial={undefined} />)
    expect(screen.getByText('Probing…')).toBeInTheDocument()
  })
})
