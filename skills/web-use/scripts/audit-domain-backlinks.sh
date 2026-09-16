#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "$0")/.." && pwd)"
skills_root="$(cd "$skill_dir/.." && pwd)"

if (( $# > 0 )); then
  domains=("$@")
else
  domains=(shop-agent food-ordering flight-search lodging-search x-twitter-kit coingecko coinmarketcap spotify-player bottom-feeder)
fi

checked=0
failed=0
for name in "${domains[@]}"; do
  file="$skills_root/$name/SKILL.md"
  [[ -f "$file" ]] || continue
  checked=$((checked + 1))
  if rg -q 'web-use' "$file"; then
    printf 'PASS: %s backlinks web-use\n' "$name"
  else
    printf 'FAIL: %s has no web-use backlink\n' "$name" >&2
    failed=$((failed + 1))
  fi
done

printf 'Checked %d installed domain skills; %d failed\n' "$checked" "$failed"
(( failed == 0 ))
