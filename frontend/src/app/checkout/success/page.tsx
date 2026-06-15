"use client";

import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Suspense, useEffect } from "react";

import { clearCart } from "@/components/cart-provider";

function SuccessInner() {
  const params = useSearchParams();
  const order = params.get("order");
  // Payment cleared but the last unit was taken first (backend sold-out path, ADR-0011).
  const soldOut = params.get("outcome") === "sold_out";

  // The checkout is over either way — empty the bag.
  useEffect(() => {
    clearCart();
  }, []);

  if (soldOut) {
    return (
      <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#FAFAF8] px-6 text-center text-[#1A1A1A]">
        <span className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-amber-100 text-2xl">
          ✕
        </span>
        <h1 className="text-3xl font-bold tracking-tight">Just sold out</h1>
        <p className="max-w-sm text-zinc-600">
          The last one sold out while your payment was going through
          {order && (
            <>
              {" "}
              (order <span className="font-medium">{order}</span>)
            </>
          )}
          . You won&apos;t be charged — any payment will be refunded.
        </p>
        <Link href="/" className="mt-2 text-sm underline underline-offset-4">
          Back to the collection
        </Link>
      </main>
    );
  }

  return (
    <main className="flex min-h-screen flex-col items-center justify-center gap-4 bg-[#FAFAF8] px-6 text-center text-[#1A1A1A]">
      <span className="inline-flex h-12 w-12 items-center justify-center rounded-full bg-lime-400 text-2xl">
        ✓
      </span>
      <h1 className="text-3xl font-bold tracking-tight">Order confirmed</h1>
      {order && (
        <p className="text-zinc-600">
          Your order <span className="font-medium">{order}</span> is paid. Thank you!
        </p>
      )}
      <Link href="/" className="mt-2 text-sm underline underline-offset-4">
        Continue shopping
      </Link>
    </main>
  );
}

export default function CheckoutSuccessPage() {
  return (
    <Suspense>
      <SuccessInner />
    </Suspense>
  );
}
