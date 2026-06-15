import Link from "next/link";

import { ProductCard } from "@/components/product-card";
import { WarmUpPing } from "@/components/warm-up-ping";
import { fetchProducts } from "@/lib/api";

const CATEGORIES = ["Tops", "Bottoms", "Outerwear", "Dresses", "Accessories"];

export default async function Home({
  searchParams,
}: {
  searchParams: Promise<{ category?: string }>;
}) {
  const { category } = await searchParams;
  const products = await fetchProducts(category);

  return (
    <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 text-[#1A1A1A] sm:px-10">
      <WarmUpPing />

      <header className="mb-10">
        <Link href="/">
          <h1 className="text-5xl font-bold tracking-tight sm:text-7xl">
            Thread It<span className="text-lime-400">.</span>
          </h1>
        </Link>
      </header>

      <nav className="mb-10 flex flex-wrap gap-x-6 gap-y-2 text-sm">
        <CategoryLink label="All" href="/" active={!category} />
        {CATEGORIES.map((c) => (
          <CategoryLink
            key={c}
            label={c}
            href={`/?category=${encodeURIComponent(c)}`}
            active={category === c}
          />
        ))}
      </nav>

      {products.length === 0 ? (
        <p className="py-24 text-center text-zinc-500">
          Nothing here yet{category ? ` in ${category}` : ""}.
        </p>
      ) : (
        <div className="grid grid-cols-2 gap-x-5 gap-y-10 md:grid-cols-3 lg:grid-cols-4">
          {products.map((p) => (
            <ProductCard key={p.slug} product={p} />
          ))}
        </div>
      )}
    </main>
  );
}

function CategoryLink({ label, href, active }: { label: string; href: string; active: boolean }) {
  return (
    <Link
      href={href}
      className={
        active
          ? "font-medium text-[#1A1A1A] underline underline-offset-4"
          : "text-zinc-500 hover:text-[#1A1A1A]"
      }
    >
      {label}
    </Link>
  );
}
