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
  is_active: boolean;
  images: ProductImage[];
  variants: Variant[];
};

// Catalog reads are cached and revalidated periodically (not per-request) so the
// storefront serves from Next's data cache instead of hitting a function→Render on
// every view — faster, cheaper, and resilient to backend cold starts. Catalog edits
// (admin) surface within CATALOG_REVALIDATE_SECONDS. Purchase paths re-validate fresh.
const CATALOG_REVALIDATE_SECONDS = 60;

export async function fetchProducts(category?: string): Promise<ProductSummary[]> {
  const url = new URL(`${API_URL}/products`);
  if (category) url.searchParams.set("category", category);
  const res = await fetch(url, { next: { revalidate: CATALOG_REVALIDATE_SECONDS } });
  if (!res.ok) throw new Error(`Failed to load products (${res.status})`);
  return res.json();
}

export async function fetchProduct(slug: string): Promise<ProductDetail | null> {
  const res = await fetch(`${API_URL}/products/${slug}`, {
    next: { revalidate: CATALOG_REVALIDATE_SECONDS },
  });
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

// ---- Checkout (ADR-0007) ----

export type CheckoutCustomer = {
  name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  postcode: string;
};

// Thrown on 409 — the cart changed (stock/availability) since it was priced.
export class CartChangedError extends Error {
  priced: PricedCart;
  constructor(priced: PricedCart) {
    super("Your bag changed");
    this.priced = priced;
  }
}

export async function checkout(
  items: CartLineInput[],
  customer: CheckoutCustomer,
  idempotencyKey?: string,
): Promise<{ gateway_url: string; order_number: string }> {
  // Idempotency-Key dedupes a double-clicked / retried checkout into one order (ADR-0013).
  const res = await fetch(`${API_URL}/checkout`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      ...(idempotencyKey ? { "Idempotency-Key": idempotencyKey } : {}),
    },
    body: JSON.stringify({ items, customer }),
  });
  if (res.status === 409) throw new CartChangedError(await res.json());
  if (!res.ok) throw new Error(`Checkout failed (${res.status})`);
  return res.json();
}

// ---- Admin (JWT bearer; ADR-0005) ----

export class UnauthorizedError extends Error {}

export type AdminVariantInput = { size: string; stock: number };
export type AdminImageInput = { url: string; alt: string; position: number };
export type ProductInput = {
  name: string;
  description: string;
  price: number;
  category: string;
  is_active: boolean;
  variants: AdminVariantInput[];
  images: AdminImageInput[];
};

export async function adminLogin(username: string, password: string): Promise<string> {
  const res = await fetch(`${API_URL}/admin/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ username, password }),
  });
  if (res.status === 401) throw new UnauthorizedError("Invalid username or password");
  if (!res.ok) throw new Error(`Login failed (${res.status})`);
  return (await res.json()).access_token;
}

async function adminFetch(token: string, path: string, init: RequestInit = {}) {
  const res = await fetch(`${API_URL}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
      ...(init.headers ?? {}),
    },
  });
  if (res.status === 401) throw new UnauthorizedError("Session expired");
  if (!res.ok) throw new Error(`Request failed (${res.status})`);
  return res;
}

export async function adminListProducts(token: string): Promise<ProductDetail[]> {
  return (await adminFetch(token, "/admin/products")).json();
}

export type OrderItem = {
  product_name: string;
  size: string;
  unit_price: number;
  quantity: number;
};

export type Order = {
  order_number: string;
  status: string;
  name: string;
  email: string;
  phone: string;
  address: string;
  city: string;
  postcode: string;
  total: number;
  currency: string;
  created_at: string;
  items: OrderItem[];
};

export async function adminListOrders(token: string): Promise<Order[]> {
  return (await adminFetch(token, "/admin/orders")).json();
}

export async function adminCreateProduct(
  token: string,
  input: ProductInput,
): Promise<ProductDetail> {
  return (
    await adminFetch(token, "/admin/products", {
      method: "POST",
      body: JSON.stringify(input),
    })
  ).json();
}

export async function adminUpdateProduct(
  token: string,
  slug: string,
  input: ProductInput,
): Promise<ProductDetail> {
  return (
    await adminFetch(token, `/admin/products/${slug}`, {
      method: "PATCH",
      body: JSON.stringify(input),
    })
  ).json();
}
