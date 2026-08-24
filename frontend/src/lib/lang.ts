import { createContext, useContext } from 'react'
import { STRINGS, type Strings } from './strings'

export type Lang = keyof typeof STRINGS

const STORAGE_KEY = 'pca-lang'

export function loadLang(): Lang {
  try {
    const raw = localStorage.getItem(STORAGE_KEY)
    return raw && raw in STRINGS ? (raw as Lang) : 'en'
  } catch {
    return 'en'
  }
}

export function saveLang(lang: Lang): void {
  try {
    localStorage.setItem(STORAGE_KEY, lang)
  } catch {
    // storage unavailable; selection simply will not persist
  }
}

export const LangContext = createContext<{ lang: Lang; setLang: (lang: Lang) => void }>({
  lang: 'en',
  setLang: () => {},
})

export function useI18n(): { lang: Lang; setLang: (lang: Lang) => void; t: Strings } {
  const { lang, setLang } = useContext(LangContext)
  return { lang, setLang, t: STRINGS[lang] }
}
