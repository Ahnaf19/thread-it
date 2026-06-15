"use client";

import { useSyncExternalStore } from "react";

// Admin JWT held client-side (ADR-0005): localStorage + useSyncExternalStore.
const KEY = "thread-it-admin-token";
const listeners = new Set<() => void>();

let cache: string | null = null;
let loaded = false;

function read(): string | null {
  if (!loaded) {
    loaded = true;
    try {
      cache = localStorage.getItem(KEY);
    } catch {
      cache = null;
    }
  }
  return cache;
}

export function setToken(token: string) {
  cache = token;
  try {
    localStorage.setItem(KEY, token);
  } catch {
    /* ignore */
  }
  listeners.forEach((l) => l());
}

export function clearToken() {
  cache = null;
  try {
    localStorage.removeItem(KEY);
  } catch {
    /* ignore */
  }
  listeners.forEach((l) => l());
}

export function getToken(): string | null {
  return read();
}

export function useAdminToken(): string | null {
  return useSyncExternalStore(
    (cb) => {
      listeners.add(cb);
      return () => listeners.delete(cb);
    },
    () => read(),
    () => null,
  );
}
