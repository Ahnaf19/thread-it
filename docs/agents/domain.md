# Domain Docs

How the engineering skills should consume this repo's domain documentation when exploring the codebase. **This is a multi-context (monorepo) repo** with separate `backend/` and `frontend/` contexts.

## Before exploring, read these

- **`CONTEXT-MAP.md`** at the repo root — it points at one `CONTEXT.md` per context. Read each one relevant to the topic.
- The per-context **`CONTEXT.md`** under `backend/` and/or `frontend/`, depending on what you're working on.
- **`docs/adr/`** — system-wide architectural decisions. Also check `backend/docs/adr/` and `frontend/docs/adr/` for context-scoped decisions.

If any of these files don't exist, **proceed silently**. Don't flag their absence; don't suggest creating them upfront. The producer skill (`/grill-with-docs`) creates them lazily when terms or decisions actually get resolved.

## File structure

Multi-context layout for this repo (presence of `CONTEXT-MAP.md` at the root signals multi-context):

```
/
├── CONTEXT-MAP.md                     ← points at each context's CONTEXT.md
├── docs/adr/                          ← system-wide decisions
├── backend/
│   ├── CONTEXT.md
│   └── docs/adr/                      ← backend-specific decisions
└── frontend/
    ├── CONTEXT.md
    └── docs/adr/                      ← frontend-specific decisions
```

## Use the glossary's vocabulary

When your output names a domain concept (in an issue title, a refactor proposal, a hypothesis, a test name), use the term as defined in the relevant `CONTEXT.md`. Don't drift to synonyms the glossary explicitly avoids.

If the concept you need isn't in the glossary yet, that's a signal — either you're inventing language the project doesn't use (reconsider) or there's a real gap (note it for `/grill-with-docs`).

## Flag ADR conflicts

If your output contradicts an existing ADR, surface it explicitly rather than silently overriding:

> _Contradicts ADR-0007 (event-sourced orders) — but worth reopening because…_
