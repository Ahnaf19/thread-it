"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

import { useAdminToken } from "@/components/admin-auth";
import { ProductForm } from "@/components/product-form";
import { adminCreateProduct, type ProductInput } from "@/lib/api";

export default function NewProductPage() {
  const router = useRouter();
  const token = useAdminToken();

  useEffect(() => {
    if (token === null) router.replace("/admin/login");
  }, [token, router]);

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
