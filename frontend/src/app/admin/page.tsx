"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { clearToken } from "@/components/admin-auth";
import { ErrorState, TableSkeleton } from "@/components/state-views";
import { Button } from "@/components/ui/button";
import { adminListProducts } from "@/lib/api";
import { formatTaka } from "@/lib/format";
import { useAdminResource } from "@/lib/use-admin";

export default function AdminProductsPage() {
  const router = useRouter();
  const { token, status, data: products, reload } = useAdminResource(adminListProducts);

  if (!token) return null;

  return (
    <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 text-[#1A1A1A] sm:px-10">
      <div className="mb-8 flex items-center justify-between">
        <h1 className="text-3xl font-bold tracking-tight">Products</h1>
        <div className="flex items-center gap-3">
          <Link href="/admin/orders" className="text-sm underline underline-offset-4">
            Orders
          </Link>
          <Link href="/admin/products/new">
            <Button className="bg-lime-400 text-[#1A1A1A] hover:bg-lime-500">New product</Button>
          </Link>
          <Button
            variant="outline"
            onClick={() => {
              clearToken();
              router.replace("/admin/login");
            }}
          >
            Log out
          </Button>
        </div>
      </div>

      {status === "error" ? (
        <ErrorState
          message="Couldn’t load products — the store may be waking up. Try again in a moment."
          onRetry={reload}
        />
      ) : status !== "ready" ? (
        <TableSkeleton />
      ) : products.length === 0 ? (
        <p className="text-zinc-500">No products yet.</p>
      ) : (
        <table className="w-full text-sm">
          <thead className="text-left text-zinc-500">
            <tr className="border-b border-black/10">
              <th className="py-2">Name</th>
              <th>Category</th>
              <th>Price</th>
              <th>Stock</th>
              <th>Status</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {products.map((p) => (
              <tr key={p.slug} className="border-b border-black/5">
                <td className="py-3 font-medium">{p.name}</td>
                <td>{p.category}</td>
                <td>{formatTaka(p.price)}</td>
                <td>{p.variants.reduce((n, v) => n + v.stock, 0)}</td>
                <td>{p.is_active ? "Active" : "Draft"}</td>
                <td className="text-right">
                  <Link
                    href={`/admin/products/${p.slug}/edit`}
                    className="underline underline-offset-4"
                  >
                    Edit
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </main>
  );
}
