import Image from "next/image";
import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import type { ProductSummary } from "@/lib/api";
import { formatTaka } from "@/lib/format";

export function ProductCard({ product }: { product: ProductSummary }) {
  const soldOut = !product.in_stock;
  return (
    <Link href={`/products/${product.slug}`} className="group block">
      <div className="relative aspect-[4/5] overflow-hidden bg-zinc-100">
        {product.primary_image ? (
          <Image
            src={product.primary_image.url}
            alt={product.primary_image.alt}
            fill
            sizes="(max-width: 640px) 50vw, (max-width: 1024px) 33vw, 25vw"
            className="object-cover transition-transform duration-300 group-hover:scale-105"
          />
        ) : (
          <div className="flex h-full items-center justify-center text-zinc-400">No image</div>
        )}
        {product.is_new && !soldOut && (
          <Badge className="absolute left-3 top-3 bg-lime-400 text-[#1A1A1A] hover:bg-lime-400">
            NEW
          </Badge>
        )}
        {soldOut && (
          <div className="absolute inset-0 flex items-center justify-center bg-white/60">
            <span className="text-sm font-medium uppercase tracking-wide text-[#1A1A1A]">
              Sold out
            </span>
          </div>
        )}
      </div>
      <div className="mt-3 flex items-baseline justify-between gap-2">
        <h3 className="text-sm font-medium text-[#1A1A1A]">{product.name}</h3>
        <span className="text-sm text-zinc-600">{formatTaka(product.price)}</span>
      </div>
    </Link>
  );
}
