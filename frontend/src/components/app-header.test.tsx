import { render, screen } from '@testing-library/react'
import { describe, expect, it } from 'vitest'
import { LangContext } from '@/lib/lang'
import { AppHeader } from './app-header'

const props = {
  showReference: true,
  onToggleReference: () => {},
  deviceConnected: true,
  deviceSerial: 'PCA-0302',
}

describe('AppHeader language', () => {
  it('renders English by default without a provider', () => {
    render(<AppHeader {...props} />)
    expect(screen.getByText('Cinema calibration colorimeter')).toBeInTheDocument()
    expect(screen.getByText('Meter connected')).toBeInTheDocument()
  })

  it('renders Czech under a cs provider', () => {
    render(
      <LangContext.Provider value={{ lang: 'cs', setLang: () => {} }}>
        <AppHeader {...props} />
      </LangContext.Provider>,
    )
    expect(screen.getByText('Kolorimetr pro kalibraci kina')).toBeInTheDocument()
  })

  it('renders the language selector', () => {
    render(<AppHeader {...props} />)
    expect(screen.getByRole('combobox', { name: 'Language' })).toBeInTheDocument()
  })
})
