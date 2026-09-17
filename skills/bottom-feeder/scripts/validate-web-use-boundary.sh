#!/usr/bin/env bash
set -euo pipefail

root_dir="$(cd "$(dirname "$0")/.." && pwd)"
cd "$root_dir"

fail() {
  printf 'FAIL: %s\n' "$1" >&2
  exit 1
}

[[ -f SKILL.md ]] || fail "missing SKILL.md"
[[ -f references/web-use-boundary.md ]] || fail "missing web-use boundary"
[[ ! -e config/run-policy.md ]] || fail "stale active run-policy.md is authoritative"

rg -q 'Load `web-use` for generic retrieval' SKILL.md || fail "missing web-use backlink"
rg -q 'must not maintain a competing universal provider ladder' SKILL.md || fail "missing ownership guard"
rg -q 'web-use` owns transport' SKILL.md || fail "missing transport ownership"

if rg -n -i 'Brave search as primary|Default: Brave|all available sources enabled|uses everything aggressively|Run 2-3 differently-worded queries|source_plan: \[knowledge-search, brave, browser\]' \
  SKILL.md README.md config references; then
  fail "stale provider ladder or ritual-all-tools instruction"
fi

rg -q 'source categor' references/web-use-boundary.md || fail "boundary is not category-first"
rg -q 'does not select web-search, browser, extraction' references/execution/provider-fallback.md || fail "generation/web routing boundary missing"

printf 'PASS: Bottom Feeder delegates generic web routing to web-use\n'
