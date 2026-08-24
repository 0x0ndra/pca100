import { render, screen } from '@testing-library/react'
import { expect, test } from 'vitest'
import { Onboarding } from './onboarding'

test('shows calibration path and both actions', () => {
  render(<Onboarding onReveal={() => {}} onReload={() => {}} />)
  expect(screen.getByText(/Application Support\/PCA-100\/calibration/)).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /open folder/i })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: /load calibration/i })).toBeInTheDocument()
})

test('shows error line only when showError is true', () => {
  const { rerender } = render(<Onboarding onReveal={() => {}} onReload={() => {}} />)
  expect(screen.queryByText(/check the folder and try again/i)).not.toBeInTheDocument()

  rerender(<Onboarding onReveal={() => {}} onReload={() => {}} showError />)
  expect(screen.getByText(/check the folder and try again/i)).toBeInTheDocument()
})
