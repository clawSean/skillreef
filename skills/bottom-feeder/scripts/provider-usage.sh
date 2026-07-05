#!/usr/bin/env bash
# Optional provider-usage probe for Bottom Feeder.
# Output: JSON snapshot of provider usage, or a benign fallback.
# Design: NEVER exit non-zero. Budget is informational only.

CORE_CLI="${TIDE_POOL_CLI:-$HOME/.openclaw/extensions/tide-pools/cli.mjs}"
LEGACY_CLI="${LOBSTER_USAGE_CLI:-$HOME/.openclaw/extensions/lobster-usage/cli.mjs}"

if [[ -f "$CORE_CLI" ]]; then
  node "$CORE_CLI" --format json 2>/dev/null && exit 0
fi
if [[ -f "$LEGACY_CLI" ]]; then
  node "$LEGACY_CLI" --format json 2>/dev/null && exit 0
fi

# Fallback: try openclaw status
raw="$(openclaw status --usage --json 2>/dev/null || true)"
if [[ -n "$raw" ]]; then
  # Try to extract JSON from potentially noisy output
  python3 -c '
import json, sys
raw = sys.argv[1]
i = raw.find("{")
if i < 0:
    raise SystemExit(0)
obj = json.loads(raw[i:])
print(json.dumps({
    "generatedAt": None,
    "providers": obj.get("usage", {}).get("providers", []),
    "venice": None,
    "available": True,
}))
' "$raw" 2>/dev/null && exit 0
fi

# Nothing worked — emit a minimal stub so callers always get valid JSON.
printf '{"available":false,"providers":[],"venice":null}\n'
