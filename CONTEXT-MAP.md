# Context Map

This monorepo has separate contexts. Each has its own glossary; read the one
relevant to what you're touching.

## Contexts

- [Backend](./backend/CONTEXT.md) — the storefront domain model and API (catalog, cart, orders, stock)

_(A `frontend/CONTEXT.md` will be added lazily when the frontend grows context-specific language.)_

## Relationships

- The **frontend** consumes the **backend** API over HTTP (CORS); it holds no domain
  rules of its own — the backend owns the model.
