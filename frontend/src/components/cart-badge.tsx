"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";

import { useCart } from "@/components/cart-provider";

export function CartBadge() {
  const pathname = usePathname();
  const { itemCount } = useCart();

  // The bag is a shopper concept — hide it across the admin surface.
  if (pathname?.startsWith("/admin")) return null;

  return (
    <Link
      href="/cart"
      className="fixed right-5 top-5 z-50 inline-flex items-center gap-2 rounded-full border border-black/10 bg-[#FAFAF8]/80 px-4 py-2 text-sm font-medium text-[#1A1A1A] backdrop-blur"
    >
      Bag
      {itemCount > 0 && (
        <span className="inline-flex h-5 min-w-5 items-center justify-center rounded-full bg-lime-400 px-1.5 text-xs font-semibold text-[#1A1A1A]">
          {itemCount}
        </span>
      )}
    </Link>
  );
}
