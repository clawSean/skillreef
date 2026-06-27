#!/usr/bin/env bash
# Baseline structural tests for telegram-ui skill
set -uo pipefail
SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SKILL_MD="$SKILL_DIR/SKILL.md"
PASS=0; FAIL=0

pass() { echo "  PASS: $1"; ((PASS++)); }
fail() { echo "  FAIL: $1"; ((FAIL++)); }

echo "=== telegram-ui baseline tests ==="

# 1. SKILL.md exists and is non-empty
if [ -s "$SKILL_MD" ]; then pass "SKILL.md exists and is non-empty"
else fail "SKILL.md missing or empty"; fi

# 2. Frontmatter has required 'name' field
if head -20 "$SKILL_MD" | grep -q '^name:'; then pass "frontmatter has 'name'"
else fail "frontmatter missing 'name'"; fi

# 3. Frontmatter has required 'description' field
if head -20 "$SKILL_MD" | grep -q '^description:'; then pass "frontmatter has 'description'"
else fail "frontmatter missing 'description'"; fi

# 4. Frontmatter name matches directory name
DIR_NAME="$(basename "$SKILL_DIR")"
FM_NAME="$(head -20 "$SKILL_MD" | grep '^name:' | sed 's/^name: *//' | tr -d '"' | tr -d "'")"
if [ "$FM_NAME" = "$DIR_NAME" ]; then pass "frontmatter name ('$FM_NAME') matches directory ('$DIR_NAME')"
else fail "frontmatter name ('$FM_NAME') does not match directory ('$DIR_NAME')"; fi

# 5. Validate all JSON code blocks are valid JSON
echo "  Checking JSON blocks..."
JSON_FAIL=0
# Extract json fenced blocks and validate each
awk '/^```json$/{ capture=1; buf=""; next } /^```$/{ if(capture){ print buf; print "---JSON_SEP---" } capture=0; next } capture{ buf = buf (buf==""?"":"\n") $0 }' "$SKILL_MD" | \
while IFS= read -r -d '' block || [ -n "$block" ]; do
  :  # handled below
done 2>/dev/null || true

# Use python for reliable multi-line JSON extraction and validation
JSON_RESULT=$(python3 -c "
import re, json, sys
text = open('$SKILL_MD').read()
blocks = re.findall(r'\`\`\`json\n(.*?)\`\`\`', text, re.DOTALL)
errors = 0
for i, b in enumerate(blocks):
    # Skip blocks with placeholders like <chat_id>
    cleaned = re.sub(r'\"<[a-z_]+>\"', '\"placeholder\"', b)
    cleaned = re.sub(r'<[a-z_]+>', '\"placeholder\"', cleaned)
    try:
        json.loads(cleaned)
    except json.JSONDecodeError as e:
        print(f'  JSON block {i+1}: INVALID - {e}', file=sys.stderr)
        errors += 1
print(f'{len(blocks)} {errors}')
" 2>&1)

TOTAL_BLOCKS=$(echo "$JSON_RESULT" | tail -1 | awk '{print $1}')
JSON_ERRORS=$(echo "$JSON_RESULT" | tail -1 | awk '{print $2}')
ERROR_LINES=$(echo "$JSON_RESULT" | head -n -1)

if [ -n "$ERROR_LINES" ]; then
  echo "$ERROR_LINES"
fi

if [ "$JSON_ERRORS" = "0" ]; then
  pass "all $TOTAL_BLOCKS JSON blocks are valid"
else
  fail "$JSON_ERRORS of $TOTAL_BLOCKS JSON blocks are invalid"
fi

# 6. Check that the skill document has key sections
for section in "Inline Buttons" "Polls" "Edits" "Replies" "Reactions" "Media" "Formatting"; do
  if grep -q "## $section" "$SKILL_MD" 2>/dev/null || grep -q "## .*$section" "$SKILL_MD" 2>/dev/null; then
    pass "has section: $section"
  else
    fail "missing expected section: $section"
  fi
done

echo ""
echo "Results: $PASS passed, $FAIL failed"
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
