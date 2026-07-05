#!/usr/bin/env bash
# Bottom Feeder helper: extract a balance number from JSON.
# Supports: .remaining | .balance | .credits | .venice.data.diem
# Design: prints a number on success, prints nothing and exits 0 on failure.
#         NEVER exits non-zero. Budget is informational only.

input="${1:-}"
if [[ -n "$input" && -f "$input" ]]; then
  data="$(cat "$input" 2>/dev/null || true)"
else
  data="$(cat 2>/dev/null || true)"
fi

[[ -z "$data" ]] && exit 0

python3 -c '
import json, sys

raw = sys.argv[1]
i = raw.find("{")
if i < 0:
    sys.exit(0)

try:
    obj = json.loads(raw[i:])
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

def pick(o, path):
    cur = o
    for k in path:
        if not isinstance(cur, dict) or k not in cur:
            return None
        cur = cur[k]
    return cur

candidates = [
    pick(obj, ["remaining"]),
    pick(obj, ["balance"]),
    pick(obj, ["credits"]),
    pick(obj, ["venice", "data", "diem"]),
]
val = next((c for c in candidates if c is not None), None)
if val is not None:
    print(f"{float(val):.4f}")
' "$data" 2>/dev/null || true
