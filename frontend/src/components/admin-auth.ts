"use client";

import { createPersistentStore } from "@/lib/persistent-store";

// Admin JWT held client-side (ADR-0005) — a thin adapter over persistent-store.
// Raw-string codec (not JSON) so the stored token format is unchanged.
const store = createPersistentStore<string | null>("thread-it-admin-token", null, {
  serialize: (v) => v ?? "",
  deserialize: (s) => s || null,
});

export function setToken(token: string) {
  store.set(token);
}

export function clearToken() {
  store.set(null);
}

export function getToken(): string | null {
  return store.get();
}

export function useAdminToken(): string | null {
  return store.useValue();
}
