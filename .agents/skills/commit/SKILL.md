---
name: commit
description: Turn a dirty git work tree into clean, atomic commits — review the diff, split unrelated changes into separate commits, run pre-commit safety checks, write conventional messages, then optionally push. Use when the user asks to commit, "commit my changes", "commit the work tree", wants help staging/splitting changes, or mentions making a commit/checkpoint.
---

# Commit

Take an uncommitted work tree and produce clean, atomic commits without churn.

## Workflow

1. **Survey the tree.** Run the inspection commands together:
   - `git status --short` — what changed
   - `git diff --stat` and `git diff` — unstaged content
   - `git diff --cached` — anything already staged
   - `git branch --show-current` and `git log --oneline -5` — branch + message style
2. **Branch check.** If on `main`, stop and create a `feature/*` branch first
   (`git switch -c feature/<topic>`). Never commit straight to `main`.
3. **Safety check.** Run `bash scripts/precommit-check.sh` (from the skill dir).
   It fails on staged `.env`/secret files and high-entropy key patterns. Also
   run the relevant gate before committing code:
   - backend changed → `cd backend && uv run ruff check . && uv run pytest -q`
   - frontend changed → `cd frontend && npm run lint`
   Report failures and stop; don't commit broken code unless told to.
4. **Plan the split.** Group the diff into atomic commits — one logical change
   each. Keep `backend/` and `frontend/` changes in separate commits; separate
   refactors from features, config from code. Show the user the planned grouping
   before staging.
5. **Stage selectively.** For each commit, `git add <specific paths>` (or
   `git add -p` for partial-file splits) — never blind `git add -A`. Verify with
   `git diff --cached --stat` that only the intended changes are staged.
6. **Write the message** (see Messages) and `git commit`.
7. **Repeat** for each group, then `git status` to confirm a clean tree.
8. **Offer to push.** Ask before pushing. On yes:
   `git push -u origin <branch>`. Stop at the commit otherwise — don't open PRs
   unless asked.

## Messages

Conventional style matching this repo's history. Format:

```
<type>: <imperative summary, ≤72 chars>

<why the change exists — optional body, wrap at 72>

Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>
```

- Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`, `ci`.
- Summary describes the change, not the files touched. Explain *why* in the body
  when it isn't obvious. Pass multi-line messages with repeated `-m` flags.
- The `Co-Authored-By` trailer is required on every commit.

## Rules

- One logical change per commit; backend and frontend never share a commit.
- Stage explicitly and verify `--cached` before every commit.
- Never commit `.env` files or secrets — the safety script enforces this.
- Push only after explicit confirmation.
