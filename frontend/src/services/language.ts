export type AppLanguage = 'en' | 'bn';

const LANGUAGE_KEY = 'fieldshift.language';

function browserStorage(): Storage | null {
  if (typeof document === 'undefined' || typeof window === 'undefined') return null;
  try {
    return window.localStorage;
  } catch {
    return null;
  }
}

function isLanguage(value: unknown): value is AppLanguage {
  return value === 'en' || value === 'bn';
}

/**
 * Read the locally stored language preference.
 *
 * The landing-page language switch is usable before sign-in, so the choice is
 * kept locally and only mirrored to `profile.preferred_language` once the
 * farmer has an account.
 */
export function getStoredLanguage(): AppLanguage {
  const storage = browserStorage();
  const raw = storage?.getItem(LANGUAGE_KEY);
  return isLanguage(raw) ? raw : 'en';
}

export function storeLanguage(language: AppLanguage): void {
  browserStorage()?.setItem(LANGUAGE_KEY, language);
}
