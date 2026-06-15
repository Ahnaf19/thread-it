"use client";

import { useMemo, useSyncExternalStore } from "react";

import type { CartLineInput } from "@/lib/api";

// Client-side cart (ADR-0004): a tiny external store synced to localStorage and
// read via useSyncExternalStore — no Provider, SSR-safe, no setState-in-effect.
const STORAGE_KEY = "thread-it-cart";
const EMPTY: CartLineInput[] = [];

let memory: CartLineInput[] | null = null;
const listeners = new Set<() => void>();

function read(): CartLineInput[] {
  if (memory === null) {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      memory = raw ? JSON.parse(raw) : [];
    } catch {
      memory = [];
    }
  }
  return memory ?? EMPTY;
}

function write(next: CartLineInput[]) {
  memory = next;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    /* storage unavailable — keep in memory */
  }
  listeners.forEach((l) => l());
}

function subscribe(cb: () => void): () => void {
  listeners.add(cb);
  return () => listeners.delete(cb);
}

function getSnapshot(): CartLineInput[] {
  return read();
}

function getServerSnapshot(): CartLineInput[] {
  return EMPTY;
}

export function addItem(slug: string, size: string, quantity = 1) {
  const lines = read();
  const i = lines.findIndex((l) => l.slug === slug && l.size === size);
  if (i === -1) {
    write([...lines, { slug, size, quantity }]);
  } else {
    const next = [...lines];
    next[i] = { ...next[i], quantity: next[i].quantity + quantity };
    write(next);
  }
}

export function setQty(slug: string, size: string, quantity: number) {
  const lines = read();
  write(
    quantity <= 0
      ? lines.filter((l) => !(l.slug === slug && l.size === size))
      : lines.map((l) => (l.slug === slug && l.size === size ? { ...l, quantity } : l)),
  );
}

export function removeItem(slug: string, size: string) {
  write(read().filter((l) => !(l.slug === slug && l.size === size)));
}

export function clearCart() {
  write([]);
}

export function useCart() {
  const lines = useSyncExternalStore(subscribe, getSnapshot, getServerSnapshot);
  const itemCount = useMemo(() => lines.reduce((n, l) => n + l.quantity, 0), [lines]);
  return { lines, itemCount, addItem, setQty, removeItem };
}
