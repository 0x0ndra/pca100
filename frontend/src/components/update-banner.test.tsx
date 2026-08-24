import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, expect, it, vi } from 'vitest'
import { LangProvider } from '@/App'
import type { UpdateInfo } from '@/hooks/use-update'
import * as useUpdateModule from '@/hooks/use-update'
import { UpdateBanner } from './update-banner'

vi.mock('@/hooks/use-update', () => ({
  useUpdate: vi.fn(),
}))

function makeInfo(overrides: Partial<UpdateInfo> = {}): UpdateInfo {
  return {
    current: '1.0.0',
    latest: '1.1.0',
    available: true,
    release_url: 'https://github.com/0x0ndra/pca100/releases/tag/v1.1.0',
    error: null,
    download: { state: 'idle', error: null, path: null },
    ...overrides,
  }
}

function mockUseUpdate(info: UpdateInfo | null, download = vi.fn()) {
  vi.mocked(useUpdateModule.useUpdate).mockReturnValue({ info, error: false, download })
}

afterEach(() => {
  vi.resetAllMocks()
})

it('renders nothing when no update is available', () => {
  mockUseUpdate(makeInfo({ available: false, latest: null }))
  const { container } = render(
    <LangProvider>
      <UpdateBanner />
    </LangProvider>,
  )
  expect(container).toBeEmptyDOMElement()
})

it('shows the update badge when an update is available', async () => {
  mockUseUpdate(makeInfo())
  render(
    <LangProvider>
      <UpdateBanner />
    </LangProvider>,
  )
  expect(await screen.findByText(/1\.1\.0/)).toBeInTheDocument()
})

it('opens the dialog and triggers a download', async () => {
  const download = vi.fn()
  mockUseUpdate(makeInfo(), download)
  render(
    <LangProvider>
      <UpdateBanner />
    </LangProvider>,
  )
  const user = userEvent.setup()
  await user.click(await screen.findByText(/1\.1\.0/))
  const releaseLink = await screen.findByRole('link', { name: /release notes/i })
  expect(releaseLink).toHaveAttribute('href', makeInfo().release_url as string)
  expect(releaseLink).toHaveAttribute('target', '_blank')
  expect(releaseLink).toHaveAttribute('rel', expect.stringContaining('noopener'))

  await user.click(screen.getByRole('button', { name: /download and install/i }))
  expect(download).toHaveBeenCalledOnce()
})
