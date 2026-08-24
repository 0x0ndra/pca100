import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test } from 'vitest'
import { LangProvider } from '@/App'
import { LangSelect } from './lang-select'
import { STRINGS } from '@/lib/strings'

beforeEach(() => localStorage.clear())

test('lists every registered language and switches on select', async () => {
  render(<LangProvider><LangSelect /></LangProvider>)
  const select = screen.getByRole('combobox', { name: /language/i }) as HTMLSelectElement
  expect(screen.getAllByRole('option')).toHaveLength(Object.keys(STRINGS).length)
  await userEvent.selectOptions(select, 'cs')
  expect(select.value).toBe('cs')
})
