#!/usr/bin/env bash
# Pre-commit safety check: refuse to commit secrets or env files.
# Scans the STAGED diff only. Exit 0 = safe, 1 = blocked, 2 = nothing staged.
set -euo pipefail

staged=$(git diff --cached --name-only)
if [ -z "$staged" ]; then
  echo "precommit: nothing staged." >&2
  exit 2
fi

fail=0

# 1. Block env / secret-bearing filenames (allow .env.example).
while IFS= read -r f; do
  [ -z "$f" ] && continue
  case "$f" in
    *.env.example|*.env.sample|*.env.template) ;;
    *.env|.env.*|*/.env|*/.env.*|*.pem|*.key|*id_rsa*|*.p12|*.pfx|*credentials*|*secret*.json)
      echo "BLOCKED: staged sensitive file -> $f" >&2
      fail=1 ;;
  esac
done <<< "$staged"

# 2. Scan added lines for high-signal secret patterns.
patterns=(
  'AKIA[0-9A-Z]{16}'                         # AWS access key id
  '-----BEGIN [A-Z ]*PRIVATE KEY-----'       # private keys
  'sk-[A-Za-z0-9]{20,}'                       # OpenAI-style keys
  'sk-ant-[A-Za-z0-9-]{20,}'                  # Anthropic keys
  'gh[pousr]_[A-Za-z0-9]{20,}'               # GitHub tokens
  'xox[baprs]-[A-Za-z0-9-]{10,}'             # Slack tokens
  '(secret|password|passwd|api[_-]?key|token)["'"'"' ]*[:=]["'"'"' ]*[A-Za-z0-9/+_-]{16,}'
)
added=$(git diff --cached --no-color -U0 | grep '^+' | grep -v '^+++' || true)
for p in "${patterns[@]}"; do
  if hits=$(printf '%s\n' "$added" | grep -nEi -e "$p" || true); [ -n "$hits" ]; then
    echo "BLOCKED: possible secret in staged diff (pattern: $p)" >&2
    printf '%s\n' "$hits" | head -3 >&2
    fail=1
  fi
done

if [ "$fail" -ne 0 ]; then
  echo "precommit: unstage the above before committing (git restore --staged <file>)." >&2
  exit 1
fi

echo "precommit: staged changes look clean."
exit 0
