"use client";

import { useSyncExternalStore } from "react";

// One deep module behind the client stores (cart, admin token): localStorage +
// listeners + an SSR-safe snapshot, read via useSyncExternalStore. Adapters add
// only their domain mutators. Codec defaults to JSON; pass a custom one for
// values that shouldn't be JSON-wrapped (e.g. a raw token string).
type Codec<T> = { serialize: (v: T) => string; deserialize: (s: string) => T };

function jsonCodec<T>(): Codec<T> {
  return { serialize: (v) => JSON.stringify(v), deserialize: (s) => JSON.parse(s) as T };
}

export function createPersistentStore<T>(
  key: string,
  fallback: T,
  codec: Codec<T> = jsonCodec<T>(),
) {
  let cache: T = fallback;
  let loaded = false;
  const listeners = new Set<() => void>();

  function read(): T {
    if (!loaded) {
      loaded = true;
      try {
        const raw = localStorage.getItem(key);
        cache = raw === null ? fallback : codec.deserialize(raw);
      } catch {
        cache = fallback;
      }
    }
    return cache;
  }

  function set(next: T) {
    cache = next;
    loaded = true;
    try {
      localStorage.setItem(key, codec.serialize(next));
    } catch {
      /* storage unavailable — keep in memory */
    }
    listeners.forEach((l) => l());
  }

  function subscribe(cb: () => void): () => void {
    listeners.add(cb);
    return () => {
      listeners.delete(cb);
    };
  }

  function useValue(): T {
    // getServerSnapshot returns the stable fallback → no hydration mismatch.
    return useSyncExternalStore(subscribe, read, () => fallback);
  }

  return { get: read, set, useValue };
}
