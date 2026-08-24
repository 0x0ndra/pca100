import { beforeEach, describe, expect, it } from 'vitest'
import { loadLang, saveLang } from './lang'

describe('loadLang/saveLang', () => {
  beforeEach(() => localStorage.clear())

  it('defaults to en', () => {
    expect(loadLang()).toBe('en')
  })

  it('round-trips a saved language', () => {
    saveLang('cs')
    expect(loadLang()).toBe('cs')
  })

  it('ignores an unknown stored value', () => {
    localStorage.setItem('pca-lang', 'de')
    expect(loadLang()).toBe('en')
  })
})
