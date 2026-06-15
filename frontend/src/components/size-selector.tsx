"use client";

import { useState } from "react";

import { Button } from "@/components/ui/button";
import type { Variant } from "@/lib/api";

// Presentation threshold for the scarcity hint (PRD Q9) — lives on the frontend.
const LOW_STOCK_THRESHOLD = 5;

export function SizeSelector({ variants }: { variants: Variant[] }) {
  const [selected, setSelected] = useState<string | null>(null);
  const selectedVariant = variants.find((v) => v.size === selected) ?? null;
  const allSoldOut = variants.every((v) => v.stock === 0);

  return (
    <div>
      <p className="mb-2 text-sm font-medium">Size</p>
      <div className="flex flex-wrap gap-2">
        {variants.map((v) => {
          const disabled = v.stock === 0;
          const active = v.size === selected;
          return (
            <button
              key={v.size}
              type="button"
              disabled={disabled}
              onClick={() => setSelected(v.size)}
              aria-pressed={active}
              className={[
                "min-w-12 border px-3 py-2 text-sm transition-colors",
                disabled
                  ? "cursor-not-allowed border-zinc-200 text-zinc-300 line-through"
                  : active
                    ? "border-[#1A1A1A] bg-[#1A1A1A] text-white"
                    : "border-zinc-300 hover:border-[#1A1A1A]",
              ].join(" ")}
            >
              {v.size}
            </button>
          );
        })}
      </div>

      {selectedVariant &&
        selectedVariant.stock > 0 &&
        selectedVariant.stock <= LOW_STOCK_THRESHOLD && (
          <p className="mt-3 text-sm text-amber-700">
            Only {selectedVariant.stock} left in {selectedVariant.size}
          </p>
        )}

      {/* Inert until the Cart feature (#4) wires it up. */}
      <Button
        disabled={allSoldOut || !selected}
        className="mt-6 w-full bg-lime-400 text-[#1A1A1A] hover:bg-lime-500 sm:w-auto"
      >
        {allSoldOut ? "Sold out" : "Add to bag"}
      </Button>
    </div>
  );
}
