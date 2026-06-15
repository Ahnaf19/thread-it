# Admin auth: roll-your-own JWT bearer, single admin via env credentials

Admin authentication is **roll-your-own**: a single admin whose username and
**bcrypt password hash** live in environment variables (`ADMIN_USERNAME`,
`ADMIN_PASSWORD_HASH`). `POST /admin/login` verifies the password and returns a
signed **JWT** (HS256, `SECRET_KEY`, ~12h expiry). Admin endpoints require the
token via an `Authorization: Bearer <token>` header, checked by a `require_admin`
dependency. There is **no user table, no session, and no auth cookie**.

## Why

- **Single admin** (the shop owner) doesn't justify Supabase Auth or a `users` table
  yet — that complexity belongs with customer accounts (v3).
- **Bearer token, not a session cookie:** the admin UI (`*.vercel.app`) and API
  (`*.onrender.com`) are different sites, so an auth cookie would be a third-party
  cookie — blocked by Safari, deprecated by Chrome (same constraint as the cart,
  ADR-0004). A token in the `Authorization` header is unaffected and stateless.
- Credentials in env keep secrets out of the repo and need no registration flow.

## Considered and rejected

- **Supabase Auth** — attractive once customers can sign up (v3), overkill for one admin now.
- **Server-side session + cookie** — the cross-site cookie problem; also adds session storage.

## Consequences

- The frontend stores the JWT (localStorage) and attaches it to `/admin/*` calls; on
  401 / expiry it routes back to login. No refresh token — the admin re-logs in.
- The password hash is generated out-of-band (a one-liner with `bcrypt`) and pasted into
  the platform env; documented in `backend/README.md`.
- When customer accounts arrive (v3), introduce a real `users` table + role boundary;
  this ADR's single-admin shortcut is explicitly a v1 measure.
