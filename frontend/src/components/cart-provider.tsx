"use client";

import { useMemo } from "react";

import type { CartLineInput } from "@/lib/api";
import { createPersistentStore } from "@/lib/persistent-store";

// Client-side cart (ADR-0004) — a thin adapter over the persistent-store module.
const store = createPersistentStore<CartLineInput[]>("thread-it-cart", []);

export function addItem(slug: string, size: string, quantity = 1) {
  const lines = store.get();
  const i = lines.findIndex((l) => l.slug === slug && l.size === size);
  if (i === -1) {
    store.set([...lines, { slug, size, quantity }]);
  } else {
    store.set(lines.map((l, j) => (j === i ? { ...l, quantity: l.quantity + quantity } : l)));
  }
}

export function setQty(slug: string, size: string, quantity: number) {
  const lines = store.get();
  store.set(
    quantity <= 0
      ? lines.filter((l) => !(l.slug === slug && l.size === size))
      : lines.map((l) => (l.slug === slug && l.size === size ? { ...l, quantity } : l)),
  );
}

export function removeItem(slug: string, size: string) {
  store.set(store.get().filter((l) => !(l.slug === slug && l.size === size)));
}

export function clearCart() {
  store.set([]);
}

export function useCart() {
  const lines = store.useValue();
  const itemCount = useMemo(() => lines.reduce((n, l) => n + l.quantity, 0), [lines]);
  return { lines, itemCount, addItem, setQty, removeItem };
}
