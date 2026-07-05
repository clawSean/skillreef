#!/usr/bin/env bash
# Mermaid skill smoke/regression tests.
# Designed per knowledge/procedures/testing-rubric-low-stakes-projects.md:
# static-ish checks + boundary smoke + failure path, no network, no restarts.

set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RENDER_SCRIPT="$SKILL_DIR/scripts/render_mermaid.sh"
PUPPETEER_CONFIG="$SKILL_DIR/references/puppeteer-config.json"
EXAMPLES="$SKILL_DIR/references/examples.md"
FIXTURE="$SKILL_DIR/tests/fixtures/simple_flowchart.mmd"
TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

pass() { printf '✅ %s\n' "$1"; }
fail() { printf '❌ %s\n' "$1" >&2; exit 1; }

command -v mmdc >/dev/null 2>&1 || fail "mmdc is not installed or not on PATH"
mmdc --version >/dev/null 2>&1 || fail "mmdc --version failed"
pass "mmdc is available: $(mmdc --version 2>&1 | head -n 1)"

[ -x "$RENDER_SCRIPT" ] || fail "render_mermaid.sh missing or not executable"
bash -n "$RENDER_SCRIPT" || fail "render_mermaid.sh has shell syntax errors"
pass "render_mermaid.sh exists, is executable, and passes bash -n"

[ -f "$PUPPETEER_CONFIG" ] || fail "Puppeteer config missing"
grep -q -- '--no-sandbox' "$PUPPETEER_CONFIG" || fail "Puppeteer config missing --no-sandbox"
grep -q -- '--disable-setuid-sandbox' "$PUPPETEER_CONFIG" || fail "Puppeteer config missing --disable-setuid-sandbox"
pass "Puppeteer config has root-safe sandbox args"

if "$RENDER_SCRIPT" "$TMP_DIR/does-not-exist.mmd" "$TMP_DIR/out.png" >"$TMP_DIR/missing.out" 2>&1; then
  fail "render_mermaid.sh unexpectedly succeeded for missing input"
fi
grep -q "Input file" "$TMP_DIR/missing.out" || fail "missing-input error did not explain input file problem"
pass "render_mermaid.sh rejects missing input with useful error"

[ -f "$FIXTURE" ] || fail "simple Mermaid fixture missing"
"$RENDER_SCRIPT" "$FIXTURE" "$TMP_DIR/simple.png" >/tmp/mermaid-render-test.log 2>&1 || {
  cat /tmp/mermaid-render-test.log >&2
  fail "render_mermaid.sh failed to render simple fixture"
}
[ -s "$TMP_DIR/simple.png" ] || fail "render output PNG missing or empty"
file "$TMP_DIR/simple.png" | grep -qi 'PNG image data' || fail "render output is not a PNG"
pass "render_mermaid.sh renders a simple fixture to PNG"

[ -f "$EXAMPLES" ] || fail "examples.md missing"
for diagram in flowchart sequenceDiagram stateDiagram-v2 gantt; do
  grep -q "$diagram" "$EXAMPLES" || fail "examples.md missing representative diagram syntax: $diagram"
done
pass "examples include representative Mermaid diagram types"

# --- SKILL.md structural validation ---
SKILL_MD="$SKILL_DIR/SKILL.md"
[ -f "$SKILL_MD" ] || fail "SKILL.md missing"
head -1 "$SKILL_MD" | grep -q '^\-\-\-' || fail "SKILL.md missing YAML frontmatter"
grep -q '^name:' "$SKILL_MD" || fail "SKILL.md frontmatter missing 'name' field"
grep -q '^description:' "$SKILL_MD" || fail "SKILL.md frontmatter missing 'description' field"
pass "SKILL.md has valid frontmatter (name + description)"

# Verify the .skill archive exists
[ -f "$SKILL_DIR/mermaid.skill" ] || fail "mermaid.skill archive missing"
[ -s "$SKILL_DIR/mermaid.skill" ] || fail "mermaid.skill archive is empty"
pass "mermaid.skill archive present and non-empty"

# Verify SKILL.md references resolve to real files
grep -oP '(?<=scripts/)\S+' "$SKILL_MD" | sed 's/[`\x60):]//g' | head -5 | while read -r ref; do
  [ -n "$ref" ] && [ -f "$SKILL_DIR/scripts/$ref" ] || fail "SKILL.md references scripts/$ref but file is missing"
done
grep -oP '(?<=references/)\S+' "$SKILL_MD" | sed 's/[`\x60):]//g' | head -5 | while read -r ref; do
  [ -n "$ref" ] && [ -f "$SKILL_DIR/references/$ref" ] || fail "SKILL.md references references/$ref but file is missing"
done
pass "SKILL.md file references resolve to existing files"

printf '\nAll Mermaid skill tests passed.\n'
