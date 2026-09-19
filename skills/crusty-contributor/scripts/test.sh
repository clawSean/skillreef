#!/usr/bin/env bash
# Baseline structural tests for the crusty-contributor skill.
# Run from the skill directory: bash scripts/test.sh

set -euo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
PASS=0; FAIL=0

pass() { PASS=$((PASS+1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL+1)); echo "  FAIL: $1"; }

echo "=== crusty-contributor baseline tests ==="

# 1. SKILL.md exists and is non-empty
if [ -s "$SKILL_DIR/SKILL.md" ]; then
  pass "SKILL.md exists and is non-empty"
else
  fail "SKILL.md missing or empty"
fi

# 2. SKILL.md has YAML frontmatter with required fields
if head -1 "$SKILL_DIR/SKILL.md" | grep -q '^---'; then
  pass "SKILL.md starts with frontmatter delimiter"
else
  fail "SKILL.md missing frontmatter opening ---"
fi

for field in name description; do
  if sed -n '/^---$/,/^---$/p' "$SKILL_DIR/SKILL.md" | grep -q "^${field}:"; then
    pass "frontmatter has '$field' field"
  else
    fail "frontmatter missing '$field' field"
  fi
done

# 3. name field matches directory name
dir_name="$(basename "$SKILL_DIR")"
fm_name="$(sed -n '/^---$/,/^---$/p' "$SKILL_DIR/SKILL.md" | grep '^name:' | head -1 | sed 's/^name:[[:space:]]*//; s/^"//; s/"$//')"
if [ "$fm_name" = "$dir_name" ]; then
  pass "frontmatter name ('$fm_name') matches directory name"
else
  fail "frontmatter name ('$fm_name') does not match directory name ('$dir_name')"
fi

# 4. Referenced files exist
while IFS= read -r ref; do
  if [ -f "$SKILL_DIR/$ref" ]; then
    pass "referenced file exists: $ref"
  else
    fail "referenced file missing: $ref"
  fi
done <<'REFS'
references/pr-template.md
references/openclaw.md
references/edge-app.md
references/edge-app/review-proof.md
references/edge-app/cross-repo-contracts.md
references/edge-app/repository-proof.md
references/edge-app/proof-contract.md
templates/edge-app-proof-packet.md
REFS


# 5. Edge reference files stay within the workspace reading budget
while IFS= read -r ref; do
  lines="$(wc -l < "$SKILL_DIR/$ref" | tr -d ' ')"
  if [ "$lines" -le 220 ]; then
    pass "line budget: $ref ($lines <= 220)"
  else
    fail "line budget exceeded: $ref ($lines > 220)"
  fi
done <<'EDGE_REFS'
references/edge-app.md
references/edge-app/review-proof.md
references/edge-app/cross-repo-contracts.md
references/edge-app/repository-proof.md
references/edge-app/proof-contract.md
templates/edge-app-proof-packet.md
EDGE_REFS

# 6. Edge proof contract is wired into the mandatory Edge route
if grep -q 'references/edge-app/proof-contract.md' "$SKILL_DIR/references/edge-app.md"; then
  pass "Edge overlay routes every PR through the proof contract"
else
  fail "Edge overlay does not route to the proof contract"
fi

if grep -q 'templates/edge-app-proof-packet.md' "$SKILL_DIR/references/edge-app/proof-contract.md"; then
  pass "proof contract routes to the reviewer packet template"
else
  fail "proof contract does not route to the reviewer packet template"
fi

proof_states='not_required planned attempted satisfied blocked_external stale'
missing_state=0
for state in $proof_states; do
  if ! grep -q "$state" "$SKILL_DIR/references/edge-app/proof-contract.md"; then
    missing_state=1
  fi
done
if [ "$missing_state" -eq 0 ]; then
  pass "proof contract defines every required evidence state"
else
  fail "proof contract is missing a required evidence state"
fi

# 7. Edge exploration remains high-freedom while publication is deliberate
if grep -q 'Suggest and compare new API/CLI fields' "$SKILL_DIR/references/edge-app.md" &&
   grep -q 'public non-draft PR' "$SKILL_DIR/references/edge-app.md"; then
  pass "Edge overlay permits exploration and gates selected-contract publication"
else
  fail "Edge overlay does not preserve the explore-boldly/publish-carefully boundary"
fi

if grep -q 'does not gate product' "$SKILL_DIR/references/edge-app/proof-contract.md" &&
   ! grep -q 'ask the maintainer/product owner first' "$SKILL_DIR/references/edge-app.md"; then
  pass "proof contract does not throttle suggestions or local prototypes"
else
  fail "proof contract still throttles suggestions or local prototypes"
fi

# 8. No secrets patterns in any file
secrets_pattern='(AKIA[0-9A-Z]{16}|ghp_[a-zA-Z0-9]{36}|sk-[a-zA-Z0-9]{40,}|-----BEGIN (RSA |EC )?PRIVATE KEY)'
if grep -rEq "$secrets_pattern" "$SKILL_DIR/" 2>/dev/null; then
  fail "potential secret/key pattern found in skill files"
else
  pass "no secret patterns detected"
fi

# 9. OpenClaw maintenance publication stays deterministic and frozen-base bound
openclaw_overlay="$SKILL_DIR/references/openclaw.md"
maintenance_contract_ok=1
for required in \
  'openclaw-pre-pr.sh' \
  '--base "$BASE_SHA"' \
  '--no-fetch' \
  '--epoch-id "$EPOCH_ID"' \
  '--receipt "$RECEIPT_PATH"' \
  'workers never fetch or substitute a newer base' \
  'A nonzero gate blocks publication'; do
  if ! grep -Fq -- "$required" "$openclaw_overlay"; then
    maintenance_contract_ok=0
  fi
done
if [ "$maintenance_contract_ok" -eq 1 ]; then
  pass "OpenClaw maintenance publication requires frozen-base deterministic receipts"
else
  fail "OpenClaw maintenance publication contract is incomplete"
fi

if grep -Fq 'Proof Lab separately' "$openclaw_overlay" &&
   grep -Fq 'owns exact-head runtime behavior evidence' "$openclaw_overlay"; then
  pass "OpenClaw overlay keeps repository policy separate from behavior proof"
else
  fail "OpenClaw overlay blurs repository policy and behavior proof ownership"
fi

# Summary
echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
