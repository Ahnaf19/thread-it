"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { use, useEffect, useState } from "react";

import { clearToken, useAdminToken } from "@/components/admin-auth";
import { ProductForm } from "@/components/product-form";
import {
  adminListProducts,
  adminUpdateProduct,
  UnauthorizedError,
  type ProductInput,
} from "@/lib/api";

export default function EditProductPage({ params }: { params: Promise<{ slug: string }> }) {
  const { slug } = use(params);
  const router = useRouter();
  const token = useAdminToken();
  const [initial, setInitial] = useState<ProductInput | null>(null);
  const [notFound, setNotFound] = useState(false);

  useEffect(() => {
    if (token === null) {
      router.replace("/admin/login");
      return;
    }
    let active = true;
    adminListProducts(token)
      .then((products) => {
        if (!active) return;
        const p = products.find((x) => x.slug === slug);
        if (!p) {
          setNotFound(true);
          return;
        }
        setInitial({
          name: p.name,
          description: p.description,
          price: p.price,
          category: p.category,
          is_active: p.is_active,
          variants: p.variants.map((v) => ({ size: v.size, stock: v.stock })),
          images: p.images.map((i) => ({ url: i.url, alt: i.alt, position: i.position })),
        });
      })
      .catch((err) => {
        if (err instanceof UnauthorizedError) {
          clearToken();
          router.replace("/admin/login");
        }
      });
    return () => {
      active = false;
    };
  }, [token, slug, router]);

  if (!token) return null;

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
      {notFound ? (
        <p className="text-zinc-500">Product not found.</p>
      ) : initial ? (
        <ProductForm initial={initial} submitLabel="Save changes" onSubmit={handleSubmit} />
      ) : (
        <p className="text-zinc-500">Loading…</p>
      )}
    </main>
  );
}
