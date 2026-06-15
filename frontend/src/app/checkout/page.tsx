"use client";

import Link from "next/link";
import { useState } from "react";

import { useCart } from "@/components/cart-provider";
import { Button } from "@/components/ui/button";
import { CartChangedError, checkout, type CheckoutCustomer } from "@/lib/api";
import { fieldClass } from "@/lib/ui";

const EMPTY: CheckoutCustomer = {
  name: "",
  email: "",
  phone: "",
  address: "",
  city: "",
  postcode: "",
};

export default function CheckoutPage() {
  const { lines } = useCart();
  const [form, setForm] = useState<CheckoutCustomer>(EMPTY);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  function set(key: keyof CheckoutCustomer, value: string) {
    setForm((f) => ({ ...f, [key]: value }));
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError(null);
    try {
      const { gateway_url } = await checkout(lines, form);
      window.location.href = gateway_url; // hand off to SSLCOMMERZ
    } catch (err) {
      setError(
        err instanceof CartChangedError
          ? "Your bag changed (an item sold out or stock dropped). Please review it."
          : "Checkout failed — please try again.",
      );
      setBusy(false);
    }
  }

  const field = fieldClass;

  if (lines.length === 0) {
    return (
      <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 text-[#1A1A1A] sm:px-10">
        <p className="text-zinc-500">
          Your bag is empty.{" "}
          <Link href="/" className="underline underline-offset-4">
            Browse the collection
          </Link>
          .
        </p>
      </main>
    );
  }

  return (
    <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 text-[#1A1A1A] sm:px-10">
      <Link href="/cart" className="text-sm text-zinc-500 hover:text-[#1A1A1A]">
        ← Bag
      </Link>
      <h1 className="mb-8 mt-4 text-3xl font-bold tracking-tight">Checkout</h1>

      <form onSubmit={handleSubmit} className="max-w-lg space-y-5">
        <div>
          <label className="mb-1 block text-sm font-medium">Full name</label>
          <input className={field} value={form.name} onChange={(e) => set("name", e.target.value)} required />
        </div>
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="mb-1 block text-sm font-medium">Email</label>
            <input type="email" className={field} value={form.email} onChange={(e) => set("email", e.target.value)} required />
          </div>
          <div className="flex-1">
            <label className="mb-1 block text-sm font-medium">Phone</label>
            <input className={field} value={form.phone} onChange={(e) => set("phone", e.target.value)} required />
          </div>
        </div>
        <div>
          <label className="mb-1 block text-sm font-medium">Address</label>
          <input className={field} value={form.address} onChange={(e) => set("address", e.target.value)} required />
        </div>
        <div className="flex gap-4">
          <div className="flex-1">
            <label className="mb-1 block text-sm font-medium">City</label>
            <input className={field} value={form.city} onChange={(e) => set("city", e.target.value)} required />
          </div>
          <div className="flex-1">
            <label className="mb-1 block text-sm font-medium">Postcode</label>
            <input className={field} value={form.postcode} onChange={(e) => set("postcode", e.target.value)} required />
          </div>
        </div>

        {error && <p className="text-sm text-red-600">{error}</p>}

        <Button type="submit" disabled={busy} className="w-full bg-lime-400 text-[#1A1A1A] hover:bg-lime-500">
          {busy ? "Redirecting…" : "Continue to payment"}
        </Button>
        <p className="text-xs text-zinc-500">You’ll pay securely via SSLCOMMERZ (sandbox).</p>
      </form>
    </main>
  );
}
