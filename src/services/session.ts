/**
 * PNMP session persistence helpers.
 *
 * The JWT access token is persisted in localStorage (set by apiService) so a
 * page refresh does NOT log the user out. The user profile is persisted
 * alongside it ONLY to restore the UI after a refresh; the authoritative
 * identity/role always comes from the backend (/users/me) on every protected
 * request — this client copy is never used for authorization decisions.
 */

const TOKEN_KEY = 'pnmp_token';
const USER_KEY = 'pnmp_user';

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string | null): void {
  if (token) localStorage.setItem(TOKEN_KEY, token);
  else localStorage.removeItem(TOKEN_KEY);
}

export function getStoredUser<T = unknown>(): T | null {
  try {
    const raw = localStorage.getItem(USER_KEY);
    return raw ? (JSON.parse(raw) as T) : null;
  } catch {
    return null;
  }
}

export function setStoredUser(user: unknown | null): void {
  if (user) localStorage.setItem(USER_KEY, JSON.stringify(user));
  else localStorage.removeItem(USER_KEY);
}

export function clearSession(): void {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}
