import Image from "next/image";
import Link from "next/link";
import { notFound } from "next/navigation";

import { Badge } from "@/components/ui/badge";
import { SizeSelector } from "@/components/size-selector";
import { WarmUpPing } from "@/components/warm-up-ping";
import { fetchProduct } from "@/lib/api";
import { formatTaka } from "@/lib/format";

export default async function ProductDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = await params;
  const product = await fetchProduct(slug);
  if (!product) notFound();

  return (
    <main className="min-h-screen bg-[#FAFAF8] px-6 py-12 text-[#1A1A1A] sm:px-10">
      <WarmUpPing />

      <Link href="/" className="text-sm text-zinc-500 hover:text-[#1A1A1A]">
        ← Back
      </Link>

      <div className="mt-6 grid gap-10 md:grid-cols-2">
        {/* Images */}
        <div className="flex flex-col gap-4">
          {product.images.length > 0 ? (
            product.images.map((img) => (
              <div key={img.position} className="relative aspect-[4/5] overflow-hidden bg-zinc-100">
                <Image
                  src={img.url}
                  alt={img.alt}
                  fill
                  sizes="(max-width: 768px) 100vw, 50vw"
                  className="object-cover"
                  priority={img.position === 0}
                />
              </div>
            ))
          ) : (
            <div className="flex aspect-[4/5] items-center justify-center bg-zinc-100 text-zinc-400">
              No image
            </div>
          )}
        </div>

        {/* Info */}
        <div className="md:sticky md:top-12 md:self-start">
          {product.is_new && (
            <Badge className="mb-3 bg-lime-400 text-[#1A1A1A] hover:bg-lime-400">NEW</Badge>
          )}
          <h1 className="text-3xl font-bold tracking-tight sm:text-4xl">{product.name}</h1>
          <p className="mt-2 text-xl text-zinc-700">{formatTaka(product.price)}</p>
          <p className="mt-6 max-w-prose leading-7 text-zinc-600">{product.description}</p>

          <div className="mt-8">
            <SizeSelector variants={product.variants} />
          </div>
        </div>
      </div>
    </main>
  );
}
