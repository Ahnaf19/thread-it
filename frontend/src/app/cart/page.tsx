"use client";

import Image from "next/image";
import Link from "next/link";
import { useEffect, useState } from "react";

import { useCart } from "@/components/cart-provider";
import { Button } from "@/components/ui/button";
import { priceCart, type PricedCart } from "@/lib/api";
import { formatTaka } from "@/lib/format";

export default function CartPage() {
  const { lines, setQty, removeItem } = useCart();
  const [priced, setPriced] = useState<PricedCart | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    if (lines.length === 0) return;
    const controller = new AbortController();
    let active = true;
    priceCart(lines, controller.signal)
      .then((p) => {
        if (active) {
          setPriced(p);
          setError(false);
        }
      })
      .catch((e) => {
        if (active && e.name !== "AbortError") setError(true);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [lines]);

  return (
    <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 text-[#1A1A1A] sm:px-10">
      <Link href="/" className="text-sm text-zinc-500 hover:text-[#1A1A1A]">
        ← Continue shopping
      </Link>
      <h1 className="mb-8 mt-4 text-4xl font-bold tracking-tight">Your bag</h1>

      {lines.length === 0 ? (
        <p className="py-20 text-zinc-500">Your bag is empty.</p>
      ) : error ? (
        <p className="py-20 text-red-600">Couldn’t price your bag — try again in a moment.</p>
      ) : loading && !priced ? (
        <p className="py-20 text-zinc-500">Pricing your bag…</p>
      ) : priced ? (
        <div className="grid gap-10 lg:grid-cols-[1fr_320px]">
          <ul className="divide-y divide-black/10">
            {priced.items.map((line) => {
              const unavailable = line.status === "unavailable";
              return (
                <li key={`${line.slug}-${line.size}`} className="flex gap-4 py-5">
                  <div className="relative h-24 w-20 shrink-0 overflow-hidden bg-zinc-100">
                    {line.primary_image && (
                      <Image
                        src={line.primary_image.url}
                        alt={line.primary_image.alt}
                        fill
                        sizes="80px"
                        className="object-cover"
                      />
                    )}
                  </div>
                  <div className="flex flex-1 flex-col">
                    <div className="flex justify-between gap-2">
                      <div>
                        <p className="font-medium">{line.name}</p>
                        <p className="text-sm text-zinc-500">Size {line.size}</p>
                      </div>
                      <button
                        onClick={() => removeItem(line.slug, line.size)}
                        className="text-sm text-zinc-400 hover:text-[#1A1A1A]"
                        aria-label="Remove"
                      >
                        Remove
                      </button>
                    </div>

                    {unavailable ? (
                      <p className="mt-2 text-sm text-red-600">No longer available</p>
                    ) : (
                      <div className="mt-auto flex items-center justify-between">
                        <div className="inline-flex items-center border border-zinc-300">
                          <button
                            onClick={() => setQty(line.slug, line.size, line.quantity - 1)}
                            className="px-3 py-1 hover:bg-zinc-100"
                            aria-label="Decrease"
                          >
                            −
                          </button>
                          <span className="min-w-8 text-center text-sm">{line.quantity}</span>
                          <button
                            onClick={() => setQty(line.slug, line.size, line.quantity + 1)}
                            disabled={line.quantity >= line.available_stock}
                            className="px-3 py-1 hover:bg-zinc-100 disabled:cursor-not-allowed disabled:text-zinc-300"
                            aria-label="Increase"
                          >
                            +
                          </button>
                        </div>
                        <span className="text-sm">{formatTaka(line.line_total)}</span>
                      </div>
                    )}
                    {line.status === "adjusted" && (
                      <p className="mt-1 text-xs text-amber-700">
                        Only {line.available_stock} available — quantity adjusted.
                      </p>
                    )}
                  </div>
                </li>
              );
            })}
          </ul>

          <aside className="h-fit border border-black/10 p-6">
            <div className="flex justify-between text-lg">
              <span>Subtotal</span>
              <span className="font-semibold">{formatTaka(priced.subtotal)}</span>
            </div>
            <p className="mt-1 text-xs text-zinc-500">Shipping calculated at checkout.</p>
            {priced.item_count > 0 ? (
              <Link
                href="/checkout"
                className="mt-5 block w-full rounded-md bg-lime-400 py-2 text-center text-sm font-medium text-[#1A1A1A] hover:bg-lime-500"
              >
                Checkout
              </Link>
            ) : (
              <Button disabled className="mt-5 w-full">
                Checkout
              </Button>
            )}
          </aside>
        </div>
      ) : null}
    </main>
  );
}
