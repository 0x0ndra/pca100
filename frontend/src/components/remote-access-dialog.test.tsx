import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { LangProvider } from '@/App'
import type { RemoteAccess } from '@/hooks/use-remote-access'
import * as useRemoteAccessModule from '@/hooks/use-remote-access'
import { RemoteAccessDialog } from './remote-access-dialog'

vi.mock('@/hooks/use-remote-access', () => ({
  useRemoteAccess: vi.fn(),
}))

function makeState(overrides: Partial<RemoteAccess> = {}): RemoteAccess {
  return {
    enabled: false,
    urls: [],
    qr: null,
    ...overrides,
  }
}

function mockUseRemoteAccess(
  state: RemoteAccess | null,
  overrides: { setEnabled?: (enabled: boolean) => void; refresh?: () => void } = {},
) {
  vi.mocked(useRemoteAccessModule.useRemoteAccess).mockReturnValue({
    state,
    error: false,
    setEnabled: overrides.setEnabled ?? vi.fn(),
    refresh: overrides.refresh ?? vi.fn(),
  })
}

afterEach(() => {
  vi.resetAllMocks()
})

it('toggling the switch calls setEnabled with the new value', async () => {
  const setEnabled = vi.fn()
  mockUseRemoteAccess(makeState(), { setEnabled })
  render(
    <LangProvider>
      <RemoteAccessDialog />
    </LangProvider>,
  )
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: /remote access/i }))
  const toggle = await screen.findByRole('switch')
  await user.click(toggle)
  await waitFor(() => expect(setEnabled).toHaveBeenCalledWith(true))
})

it('shows the connect URL and QR image when remote access is enabled', async () => {
  mockUseRemoteAccess(
    makeState({
      enabled: true,
      urls: ['http://192.168.1.20:8000'],
      qr: 'data:image/png;base64,ABC123',
    }),
  )
  render(
    <LangProvider>
      <RemoteAccessDialog />
    </LangProvider>,
  )
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: /remote access/i }))
  expect(await screen.findByText('http://192.168.1.20:8000')).toBeInTheDocument()
  const img = await screen.findByRole('img', { name: /connect qr/i })
  expect(img).toHaveAttribute('src', 'data:image/png;base64,ABC123')
})

it('shows a hint instead of an empty list when enabled but no urls are found', async () => {
  mockUseRemoteAccess(makeState({ enabled: true, urls: [] }))
  render(
    <LangProvider>
      <RemoteAccessDialog />
    </LangProvider>,
  )
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: /remote access/i }))
  expect(await screen.findByText(/no network address found/i)).toBeInTheDocument()
})

it('refreshes remote access state when the dialog opens', async () => {
  const refresh = vi.fn()
  mockUseRemoteAccess(makeState(), { refresh })
  render(
    <LangProvider>
      <RemoteAccessDialog />
    </LangProvider>,
  )
  expect(refresh).not.toHaveBeenCalled()
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: /remote access/i }))
  await waitFor(() => expect(refresh).toHaveBeenCalledOnce())
})
