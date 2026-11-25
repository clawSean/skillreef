#!/usr/bin/env bash
# Baseline structural tests for the shop-agent skill.
# No external dependencies — just bash.
set -uo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_MD="$SKILL_DIR/SKILL.md"
PASS=0
FAIL=0

pass() { ((PASS++)); echo "  PASS: $1"; }
fail() { ((FAIL++)); echo "  FAIL: $1"; }

echo "=== shop-agent baseline tests ==="

# 1. SKILL.md exists and is non-empty
echo "[1] SKILL.md exists and is non-empty"
if [[ -s "$SKILL_MD" ]]; then pass "SKILL.md present"; else fail "SKILL.md missing or empty"; fi

# 2. Frontmatter has required fields (name, description)
echo "[2] Frontmatter fields"
head -20 "$SKILL_MD" | grep -q '^name:' && pass "name field" || fail "name field missing"
head -20 "$SKILL_MD" | grep -q '^description:' && pass "description field" || fail "description field missing"

# 3. Referenced reference files exist
echo "[3] Referenced files in references/"
for f in amazon.md safety.md price-history.md purchase-monitoring.md; do
  if [[ -f "$SKILL_DIR/references/$f" ]]; then
    pass "references/$f exists"
  else
    fail "references/$f missing"
  fi
done

# 4. Retailer table references — future files are allowed to be absent,
#    but any file marked 🟡 (Building) or 🟢 should exist.
echo "[4] Building/active retailer refs exist"
while IFS='|' read -r _ retailer ref status _; do
  ref="$(echo "$ref" | xargs | tr -d '\`')"  # trim whitespace and backticks
  status="$(echo "$status" | xargs)"
  # Only check files that are marked as building or active
  if [[ "$status" == *"🟡"* || "$status" == *"🟢"* ]]; then
    target="$SKILL_DIR/$ref"
    if [[ -f "$target" ]]; then
      pass "$ref present (status: $status)"
    else
      fail "$ref missing but status is $status"
    fi
  fi
done < <(grep '^\|.*references/.*\.md' "$SKILL_MD" || true)

# 5. Safety doc mentions the core rule keywords
echo "[5] Safety doc content checks"
SAFETY="$SKILL_DIR/references/safety.md"
if [[ -f "$SAFETY" ]]; then
  grep -qi 'confirmation' "$SAFETY" && pass "safety mentions confirmation" || fail "safety missing confirmation keyword"
  grep -qi 'never' "$SAFETY" && pass "safety mentions 'never' constraints" || fail "safety missing 'never' constraints"
  grep -qi '1-click' "$SAFETY" && pass "safety covers 1-click" || fail "safety missing 1-click coverage"
else
  fail "safety.md not found"
fi

# 6. Domain references must inherit generic routing from web-use and must not
#    resurrect the contributor-specific credentials or a competing extraction ladder.
echo "[6] Portable web-use boundary"
if rg -n 'the contributor 1Password|the contributor vault|Never type credentials|Browserless first|TinyFish Browser API' \
  "$SKILL_DIR/SKILL.md" "$SKILL_DIR/references" >/dev/null; then
  fail "non-portable credential or provider-routing guidance found"
else
  pass "no non-portable credential/provider ladder guidance"
fi
grep -q 'web-use' "$SKILL_DIR/references/amazon.md" \
  && pass "Amazon reference backlinks to web-use" || fail "Amazon reference missing web-use backlink"

if rg -n "curl[^\\n]*api_key|https?://[^[:space:]\"']*api_key=" \
  "$SKILL_DIR/SKILL.md" "$SKILL_DIR/references" >/dev/null; then
  fail "secret-bearing API URL/process argument guidance found"
else
  pass "API secrets stay out of URLs and process arguments"
fi

if rg -n '^[[:space:]]*op read ' "$SKILL_DIR/SKILL.md" "$SKILL_DIR/references" >/dev/null; then
  fail "naked secret-manager read command found"
else
  pass "secret-manager references require a non-printing helper/runtime"
fi

# 7. No secrets/API keys hardcoded in any file
echo "[7] No hardcoded secrets"
if grep -rqiE '(api_key|password|secret)\s*[:=]\s*["\x27][A-Za-z0-9]{16,}' "$SKILL_DIR"; then
  fail "possible hardcoded secret found"
else
  pass "no hardcoded secrets detected"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[[ $FAIL -eq 0 ]] && exit 0 || exit 1
