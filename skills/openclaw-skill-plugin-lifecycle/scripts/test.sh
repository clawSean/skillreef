#!/usr/bin/env bash
# Baseline structural tests for the OpenClaw skill/plugin lifecycle skill.
# Run: bash scripts/test.sh
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_FILE="$SKILL_DIR/SKILL.md"
PASS=0
FAIL=0

pass() { PASS=$((PASS+1)); echo "  PASS: $1"; }
fail() { FAIL=$((FAIL+1)); echo "  FAIL: $1"; }

echo "=== openclaw-skill-plugin-lifecycle baseline tests ==="

# 1. SKILL.md exists and is non-empty
if [ -s "$SKILL_FILE" ]; then
  pass "SKILL.md exists and is non-empty"
else
  fail "SKILL.md missing or empty"
fi

# 2. SKILL.md has YAML frontmatter with required fields
if head -1 "$SKILL_FILE" | grep -q '^---$'; then
  pass "SKILL.md starts with frontmatter delimiter"
else
  fail "SKILL.md missing frontmatter opening ---"
fi

# Extract frontmatter (between first and second ---)
FRONTMATTER=$(sed -n '2,/^---$/ { /^---$/d; p; }' "$SKILL_FILE")

for field in name description; do
  if echo "$FRONTMATTER" | grep -q "^${field}:"; then
    pass "frontmatter has '${field}' field"
  else
    fail "frontmatter missing '${field}' field"
  fi
done

# 3. name field is the intentional unique OpenClaw-specific skill name.
FM_NAME=$(echo "$FRONTMATTER" | grep '^name:' | sed 's/^name:[[:space:]]*//' | tr -d '"')
EXPECTED_NAME="openclaw-skill-plugin-lifecycle"
if [ "$FM_NAME" = "$EXPECTED_NAME" ]; then
  pass "frontmatter name is the expected OpenClaw-specific skill name ('$FM_NAME')"
else
  fail "frontmatter name ('$FM_NAME') does not match expected name ('$EXPECTED_NAME')"
fi

if [ "$(basename "$SKILL_DIR")" = "$FM_NAME" ]; then
  pass "skill directory matches the runtime name"
else
  fail "skill directory does not match the runtime name"
fi

if [ "$FM_NAME" != "plugin-creator" ]; then
  pass "frontmatter name does not collide with Codex's built-in plugin-creator skill"
else
  fail "frontmatter name collides with Codex's built-in plugin-creator skill"
fi

if grep -Fq 'openclaw skills workshop apply <proposal-id> --json' "$SKILL_FILE" && \
   grep -Fq 'there is no separate' "$SKILL_FILE"; then
  pass "legacy skill approval routes through the operator CLI without an adoption step"
else
  fail "legacy skill operator apply route is missing"
fi

# 4. All files referenced in SKILL.md exist
REF_FILES=$(grep -oE '`references/[^`]+`' "$SKILL_FILE" | tr -d '`' | sort -u)
for ref in $REF_FILES; do
  if [ -f "$SKILL_DIR/$ref" ]; then
    pass "referenced file '$ref' exists"
  else
    fail "referenced file '$ref' NOT FOUND"
  fi
done

# 5. Reference files are non-empty
for ref in "$SKILL_DIR"/references/*.md; do
  bname=$(basename "$ref")
  if [ -s "$ref" ]; then
    pass "references/$bname is non-empty"
  else
    fail "references/$bname is empty"
  fi
done

# 6. No broken markdown headings (# with no space)
BAD_HEADINGS=$(grep -nE '^#{1,6}[^#[:space:]]' "$SKILL_FILE" || true)
if [ -z "$BAD_HEADINGS" ]; then
  pass "no malformed markdown headings in SKILL.md"
else
  fail "malformed markdown headings in SKILL.md: $BAD_HEADINGS"
fi

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
