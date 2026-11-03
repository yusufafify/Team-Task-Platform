import * as SecureStore from 'expo-secure-store';
import { useSyncExternalStore } from 'react';

export interface Tokens {
  access: string;
  refresh: string;
}

type Status = 'loading' | 'signedIn' | 'signedOut';

const ACCESS_KEY = 'nesma.access';
const REFRESH_KEY = 'nesma.refresh';

let tokens: Tokens | null = null;
let status: Status = 'loading';
const listeners = new Set<() => void>();

function setTokens(next: Tokens | null) {
  tokens = next;
  status = next ? 'signedIn' : 'signedOut';
  listeners.forEach((listener) => listener());
}

export function getTokens(): Tokens | null {
  return tokens;
}

export async function loadTokens(): Promise<void> {
  try {
    const [access, refresh] = await Promise.all([
      SecureStore.getItemAsync(ACCESS_KEY),
      SecureStore.getItemAsync(REFRESH_KEY),
    ]);
    setTokens(access && refresh ? { access, refresh } : null);
  } catch {
    // An unreadable keystore (e.g. after a restore) only costs a fresh sign-in.
    setTokens(null);
  }
}

// Refresh rotates the refresh token, so memory switches first and the next call already uses it.
export async function saveTokens(next: Tokens): Promise<void> {
  setTokens(next);
  await Promise.all([
    SecureStore.setItemAsync(ACCESS_KEY, next.access),
    SecureStore.setItemAsync(REFRESH_KEY, next.refresh),
  ]);
}

export async function clearTokens(): Promise<void> {
  setTokens(null);
  await Promise.all([
    SecureStore.deleteItemAsync(ACCESS_KEY),
    SecureStore.deleteItemAsync(REFRESH_KEY),
  ]);
}

function subscribe(listener: () => void) {
  listeners.add(listener);
  return () => {
    listeners.delete(listener);
  };
}

export function useSessionStatus(): Status {
  // Web's server render, and the hydration that must match it, always start at 'loading'.
  return useSyncExternalStore(subscribe, () => status, (): Status => 'loading');
}
