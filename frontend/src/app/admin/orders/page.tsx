"use client";

import Link from "next/link";
import { useState } from "react";

import { adminListOrders } from "@/lib/api";
import { formatTaka } from "@/lib/format";
import { useAdminResource } from "@/lib/use-admin";

const STATUSES = ["all", "paid", "pending", "failed", "cancelled"];

export default function AdminOrdersPage() {
  const { token, data: orders } = useAdminResource(adminListOrders);
  const [filter, setFilter] = useState("all");

  if (!token) return null;

  const shown = orders?.filter((o) => filter === "all" || o.status === filter) ?? [];

  return (
    <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 text-[#1A1A1A] sm:px-10">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Orders</h1>
        <Link href="/admin" className="text-sm underline underline-offset-4">
          Products
        </Link>
      </div>

      <nav className="mb-6 flex flex-wrap gap-x-5 gap-y-2 text-sm">
        {STATUSES.map((s) => (
          <button
            key={s}
            onClick={() => setFilter(s)}
            className={
              filter === s
                ? "font-medium capitalize underline underline-offset-4"
                : "capitalize text-zinc-500 hover:text-[#1A1A1A]"
            }
          >
            {s}
          </button>
        ))}
      </nav>

      {orders === null ? (
        <p className="text-zinc-500">Loading…</p>
      ) : shown.length === 0 ? (
        <p className="text-zinc-500">No orders.</p>
      ) : (
        <table className="w-full text-sm">
          <thead className="text-left text-zinc-500">
            <tr className="border-b border-black/10">
              <th className="py-2">Order</th>
              <th>Date</th>
              <th>Customer</th>
              <th>Items</th>
              <th>Total</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {shown.map((o) => (
              <tr key={o.order_number} className="border-b border-black/5 align-top">
                <td className="py-3 font-medium">{o.order_number}</td>
                <td>{new Date(o.created_at).toLocaleDateString()}</td>
                <td>
                  {o.name}
                  <br />
                  <span className="text-zinc-500">{o.email}</span>
                </td>
                <td>
                  {o.items.map((it, i) => (
                    <div key={i} className="text-zinc-600">
                      {it.product_name} ({it.size}) ×{it.quantity}
                    </div>
                  ))}
                </td>
                <td>{formatTaka(o.total)}</td>
                <td className="capitalize">{o.status}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
