"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";

import { ProductForm } from "@/components/product-form";
import { adminCreateProduct, type ProductInput } from "@/lib/api";
import { useRequireAdmin } from "@/lib/use-admin";

export default function NewProductPage() {
  const router = useRouter();
  const token = useRequireAdmin();

  if (!token) return null;

  async function handleSubmit(input: ProductInput) {
    await adminCreateProduct(token!, input);
    router.push("/admin");
  }

  return (
    <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 text-[#1A1A1A] sm:px-10">
      <Link href="/admin" className="text-sm text-zinc-500 hover:text-[#1A1A1A]">
        ← Products
      </Link>
      <h1 className="mb-8 mt-4 text-3xl font-bold tracking-tight">New product</h1>
      <ProductForm submitLabel="Create product" onSubmit={handleSubmit} />
    </main>
  );
}
