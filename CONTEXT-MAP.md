# Context Map

This monorepo has separate contexts. Each has its own glossary; read the one
relevant to what you're touching.

## Contexts

- [Backend](./backend/CONTEXT.md) — the storefront domain model and API (catalog, cart, orders, stock)
- [Frontend](./frontend/CONTEXT.md) — the storefront + admin UI; how fetched views behave (loading / empty / error) and how cold starts surface

## Relationships

- The **frontend** consumes the **backend** API over HTTP (CORS); it holds no domain
  rules of its own — the backend owns the model. The frontend's own language is about
  **fetch states** (Async resource, Resource status) layered over the backend's nouns.
