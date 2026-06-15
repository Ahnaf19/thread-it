"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use } from "react";

import { ProductForm } from "@/components/product-form";
import { ErrorState } from "@/components/state-views";
import { Skeleton } from "@/components/ui/skeleton";
import { adminListProducts, adminUpdateProduct, type ProductInput } from "@/lib/api";
import { useAdminResource } from "@/lib/use-admin";

export default function EditProductPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const router = useRouter();
  const { token, status, data: products, reload } = useAdminResource(adminListProducts);

  if (!token) return null;

  const product = products?.find((x) => x.slug === slug) ?? null;
  const initial: ProductInput | null = product && {
    name: product.name,
    description: product.description,
    price: product.price,
    category: product.category,
    is_active: product.is_active,
    variants: product.variants.map((v) => ({ size: v.size, stock: v.stock })),
    images: product.images.map((i) => ({ url: i.url, alt: i.alt, position: i.position })),
  };

  async function handleSubmit(input: ProductInput) {
    await adminUpdateProduct(token!, slug, input);
    router.push("/admin");
  }

  return (
    <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 text-[#1A1A1A] sm:px-10">
      <Link href="/admin" className="text-sm text-zinc-500 hover:text-[#1A1A1A]">
        ← Products
      </Link>
      <h1 className="mb-8 mt-4 text-3xl font-bold tracking-tight">Edit product</h1>
      {status === "error" ? (
        <ErrorState
          message="Couldn’t load this product — the store may be waking up. Try again in a moment."
          onRetry={reload}
        />
      ) : status !== "ready" ? (
        <Skeleton className="h-96 w-full max-w-lg" />
      ) : initial ? (
        <ProductForm initial={initial} submitLabel="Save changes" onSubmit={handleSubmit} />
      ) : (
        <p className="text-zinc-500">Product not found.</p>
      )}
    </main>
  );
}
