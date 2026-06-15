# SSLCOMMERZ integration: server-side init, redirect flow, backend callbacks

Checkout integrates SSLCOMMERZ (sandbox) with the **redirect-based** flow:

1. The browser `POST`s the cart + customer info to **`POST /checkout`**. The backend
   re-prices/re-validates the cart (never trusts client prices), creates a `pending`
   Order, and calls the SSLCOMMERZ **session-init API server-side** (`httpx`) using
   `tran_id = order_number`.
2. The init returns a `GatewayPageURL`; the backend returns it as JSON and the browser
   redirects there to pay.
3. SSLCOMMERZ's `success_url` / `fail_url` / `cancel_url` / `ipn_url` point at **backend**
   endpoints (it POSTs to them). They update the Order, then **302-redirect the browser
   to the frontend** return pages (`/checkout/success|fail|cancel`).

## Why

- **Server-side init + re-pricing** keeps store credentials and the authoritative total
  on the backend; the client can't tamper with the amount.
- **Callbacks hit the backend, not the frontend**, because SSLCOMMERZ POSTs form data to
  them — a static Vercel page can't receive that. The backend handles it, then redirects
  the browser onward to the frontend screen.
- **`tran_id = order_number`** ties every gateway transaction back to one Order.

## Consequences / config

- Env: `SSLCOMMERZ_STORE_ID`, `SSLCOMMERZ_STORE_PASSWORD`, the sandbox base URL, and
  `FRONTEND_URL` (for the final browser redirect). Secrets in platform env only.
- The HTTP call is behind a small client so tests **mock** it — tests never hit the real
  gateway; the live sandbox is verified post-deploy.
- v1 trusts the callback's posted `status` + amount and marks paid (guarded). The separate
  server-side validation-API call and exactly-once IPN handling are **v2**.
