// Backend API base URL. Set NEXT_PUBLIC_API_URL in Vercel env settings to the
// Render backend URL (e.g. https://thread-it-api.onrender.com). Falls back to
// the local FastAPI dev server.
export const API_URL =
  process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Health = {
  status: string;
  service: string;
  environment: string;
};

// Cold-start warm-up: Render's free tier spins down after ~15 min idle, so the
// next request waits ~30-50s while it boots. We ping /health on page load to
// warm it while the user reads the page. A mitigation, not a fix.
export async function fetchHealth(signal?: AbortSignal): Promise<Health> {
  const res = await fetch(`${API_URL}/health`, { signal });
  if (!res.ok) {
    throw new Error(`Backend returned ${res.status}`);
  }
  return res.json();
}

// ---- Catalog ----

export type PrimaryImage = { url: string; alt: string };

export type ProductSummary = {
  slug: string;
  name: string;
  price: number;
  currency: string;
  category: string;
  is_new: boolean;
  primary_image: PrimaryImage | null;
  in_stock: boolean;
};

export type ProductImage = { url: string; alt: string; position: number };
export type Variant = { size: string; stock: number };

export type ProductDetail = {
  slug: string;
  name: string;
  description: string;
  price: number;
  currency: string;
  category: string;
  is_new: boolean;
  images: ProductImage[];
  variants: Variant[];
};

// Catalog reads are dynamic (no-store) in v1 — caching is a v4 concern, and it
// keeps `next build` from hitting the API at build time.
export async function fetchProducts(category?: string): Promise<ProductSummary[]> {
  const url = new URL(`${API_URL}/products`);
  if (category) url.searchParams.set("category", category);
  const res = await fetch(url, { cache: "no-store" });
  if (!res.ok) throw new Error(`Failed to load products (${res.status})`);
  return res.json();
}

export async function fetchProduct(slug: string): Promise<ProductDetail | null> {
  const res = await fetch(`${API_URL}/products/${slug}`, { cache: "no-store" });
  if (res.status === 404) return null;
  if (!res.ok) throw new Error(`Failed to load product (${res.status})`);
  return res.json();
}

// ---- Cart (stateless pricing; ADR-0004) ----

export type CartLineInput = { slug: string; size: string; quantity: number };
export type LineStatus = "ok" | "adjusted" | "unavailable";

export type PricedLine = {
  slug: string;
  name: string;
  size: string;
  primary_image: PrimaryImage | null;
  unit_price: number;
  quantity: number;
  line_total: number;
  available_stock: number;
  status: LineStatus;
};

export type PricedCart = {
  items: PricedLine[];
  subtotal: number;
  currency: string;
  item_count: number;
};

// Called from the browser (cross-origin; covered by CORS for the prod origin).
export async function priceCart(
  items: CartLineInput[],
  signal?: AbortSignal,
): Promise<PricedCart> {
  const res = await fetch(`${API_URL}/cart`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ items }),
    signal,
  });
  if (!res.ok) throw new Error(`Failed to price cart (${res.status})`);
  return res.json();
}
