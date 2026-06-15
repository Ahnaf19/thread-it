# Cart is client-side; the backend prices it statelessly

The Cart lives in the **browser** (held in a React context, persisted to
`localStorage`). The backend exposes a **stateless `POST /cart`** that takes the
line items, looks up current price + stock, and returns a priced, validated cart.
There is **no server-side cart storage and no cart cookie** in v1.

## Why

- The frontend (`*.vercel.app`) and backend (`*.onrender.com`) are different sites, so
  a backend-set cart cookie would be a **third-party cookie** — blocked by Safari and
  being phased out by Chrome. A cookie/session cart would be quietly unreliable.
- `localStorage` is first-party to the storefront, survives reloads, and needs no
  anonymous-cart storage or cleanup on the server.
- The roadmap wants **cart-total logic tested on the backend**; a stateless pricing
  endpoint puts the money math + stock rules there as a pure function over inputs +
  catalog data, while keeping cart *state* on the client.

## Consequences

- The cart does not follow a user across devices — acceptable for guest checkout (v1).
- `POST /cart` is called from the browser (cross-origin) — covered by existing CORS for
  the production origin; no credentials needed (no cookie).
- Line items reference a Variant by `(slug, size)`, not internal UUID, so the catalog
  API need not expose variant IDs.
- At checkout (#5) the client submits this cart to create the Order; pricing/stock are
  re-validated server-side there (the cart endpoint is advisory, not authoritative for
  payment).
