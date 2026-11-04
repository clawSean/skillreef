#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "$0")/.." && pwd)"
workspace="$(cd "$skill_dir/../.." && pwd)"
pass=0
fail=0

ok() { pass=$((pass + 1)); echo "PASS: $1"; }
bad() { fail=$((fail + 1)); echo "FAIL: $1"; }
skip() { echo "SKIP: $1"; }

required=(
  SKILL.md
  references/decision-matrix.md references/research-routing.md
  references/provider-matrix.md
  references/provider-registry.local.example.md
  references/domain-ownership.md references/domain-backlink-audit.md references/context-device.md
  references/extraction-backends.md references/shared-tab-extension.md
  references/proof-policy.md references/design-decisions.md
  references/proof-ledger.local.example.md
  assets/web-use-architecture.svg assets/web-use-routing-map.svg
)
for rel in "${required[@]}"; do
  [[ -f "$skill_dir/$rel" ]] && ok "$rel exists" || bad "$rel missing"
done

private_required=(
  VISION.md STATUS.md LOG.md DECISIONS.md RESOURCES.md
  references/provider-registry.local.md references/proof-ledger.local.md
)
if [[ -f "$skill_dir/VISION.md" ]]; then
  for rel in "${private_required[@]}"; do
    [[ -f "$skill_dir/$rel" ]] && ok "$rel exists" || bad "$rel missing"
  done
else
  skip "private canonical files intentionally absent from public mirror"
fi

bash "$skill_dir/scripts/audit-domain-backlinks.sh" >/dev/null \
  && ok "portable domain backlink audit" || bad "portable domain backlink audit"

lines="$(wc -l < "$skill_dir/SKILL.md" | tr -d ' ')"
(( lines <= 220 )) && ok "SKILL.md line budget ($lines/220)" || bad "SKILL.md too long ($lines/220)"

for marker in 'Category waterfall' 'Selective exposure' 'Lane-failure escalation' 'Ownership contract'; do
  rg -q "$marker" "$skill_dir/SKILL.md" && ok "$marker present" || bad "$marker missing"
done

rg -q 'managed browser in the stable profile' "$skill_dir/SKILL.md" \
  && rg -q 'enter a user-supplied code or one retrieved from an' "$skill_dir/SKILL.md" \
  && rg -q 'retry once through `browser-automation`' "$skill_dir/SKILL.md" \
  && ok "authentication capability path" \
  || bad "authentication capability path missing"

python3 - "$skill_dir" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
checks = {
    "SKILL.md": ("whole-desktop GUI", "shared-tab context"),
    "references/decision-matrix.md": ("GUI/computer use after display preflight", "shared-tab context, pinned"),
    "references/context-device.md": ("| Whole-desktop GUI |", "| Extension-relay shared tab |"),
    "references/provider-matrix.md": ("| Native GUI/OS |", "| Extension-relay shared tab |"),
}
for rel, (gui, shared) in checks.items():
    text = (root / rel).read_text(encoding="utf-8")
    if gui not in text or shared not in text or text.index(gui) > text.index(shared):
        raise AssertionError(f"{rel}: GUI/computer-use lane must precede shared-tab fallback")
PY
ok "self-sufficient GUI precedes consent-bound shared-tab fallback"

python3 - "$skill_dir" <<'PY'
from pathlib import Path
import sys

root = Path(sys.argv[1])
skill = (root / "SKILL.md").read_text(encoding="utf-8")
contexts = (root / "references/context-device.md").read_text(encoding="utf-8")
providers = (root / "references/provider-matrix.md").read_text(encoding="utf-8")
shared = (root / "references/shared-tab-extension.md").read_text(encoding="utf-8")

required = {
    "SKILL.md": (skill, 'profile="user"', "Extension relay", "Shared tab"),
    "context-device.md": (contexts, "Existing-session driver", "Extension relay", "All tabs"),
    "provider-matrix.md": (providers, "existing-session", 'profile="chrome"', "All tabs"),
    "shared-tab-extension.md": (shared, "Access mode", "Selected tabs", "All tabs"),
}
for rel, (text, *markers) in required.items():
    missing = [marker for marker in markers if marker not in text]
    if missing:
        raise AssertionError(f"{rel}: missing browser-context compatibility markers: {missing}")

if "controls only explicitly shared tabs" in contexts:
    raise AssertionError("context-device.md overclaims a selected-tab boundary")
PY
ok "managed, existing-session, and extension-relay contexts stay distinct"

python3 - "$skill_dir" <<'PY'
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

root = Path(sys.argv[1])
for rel in ("assets/web-use-architecture.svg", "assets/web-use-routing-map.svg"):
    ET.parse(root / rel)

routing = (root / "assets/web-use-routing-map.svg").read_text(encoding="utf-8")
required = (
    "Computer use / GUI",
    "Shared personal tab",
    "EXPLICIT REQUEST",
    "Notify, continue through authorized controls, and verify the resulting state.",
    "stroke-dasharray",
)
if any(marker not in routing for marker in required):
    raise AssertionError("routing SVG is missing required autonomy/consent semantics")
if routing.index("Computer use / GUI") > routing.index("Shared personal tab"):
    raise AssertionError("routing SVG must place self-sufficient GUI before shared-tab fallback")
for machine_specific in ("Arc", "Dia", "Google Chrome", "Peekaboo", "Browserless", "TinyFish"):
    if machine_specific in routing:
        raise AssertionError(f"routing SVG leaked provider-specific detail: {machine_specific}")
PY
ok "repo-native SVGs parse and preserve portable routing semantics"

domain_skills=(shop-agent food-ordering flight-search lodging-search x-twitter-kit coingecko coinmarketcap spotify-player bottom-feeder)
for name in "${domain_skills[@]}"; do
  file="$workspace/skills/$name/SKILL.md"
  [[ -f "$file" ]] || { skip "$name absent from scoped mirror"; continue; }
  rg -q 'web-use' "$file" && ok "$name backlinks web-use" || bad "$name missing web-use backlink"
done

publish="$workspace/scripts/publish-skillreef.sh"
if [[ -f "$publish" ]]; then
  for private in VISION.md STATUS.md LOG.md DECISIONS.md RESOURCES.md provider-registry.local.md proof-ledger.local.md; do
    rg -q "$private" "$publish" && ok "$private excluded from public mirror" || bad "$private publish exclusion missing"
  done
else
  skip "private publisher checks unavailable in public mirror"
fi

pycache_dir="$(mktemp -d)"
trap '/usr/bin/trash "$pycache_dir" >/dev/null 2>&1 || true' EXIT
for script in "$skill_dir"/scripts/*.py; do
  PYTHONPYCACHEPREFIX="$pycache_dir" python3 -m py_compile "$script" && ok "$(basename "$script") compiles" || bad "$(basename "$script") compile"
  PYTHONPYCACHEPREFIX="$pycache_dir" python3 "$script" --help >/dev/null && ok "$(basename "$script") help" || bad "$(basename "$script") help"
done

python3 - "$skill_dir/scripts" <<'PY'
import sys
sys.path.insert(0, sys.argv[1])
import _http
response = _http.Response(200, b'{"ok": true}')
assert response.ok and response.json() == {"ok": True}
PY
ok "stdlib HTTP shim"

PYTHONPYCACHEPREFIX="$pycache_dir" python3 - "$skill_dir/scripts" <<'PY'
import os
import stat
import sys
import tempfile

sys.path.insert(0, sys.argv[1])
import browserless_extract
import browserless_session

os.environ.pop("BROWSERLESS_HOST", None)
assert browserless_extract.configured_host() == browserless_extract.DEFAULT_HOST
os.environ["BROWSERLESS_HOST"] = "https://evil.example"
try:
    browserless_extract.configured_host()
except ValueError:
    pass
else:
    raise AssertionError("untrusted Browserless host accepted")

with tempfile.TemporaryDirectory() as root:
    path = os.path.join(root, "session.json")
    browserless_session.write_session_file(path, {"id": "test"}, False)
    assert stat.S_IMODE(os.stat(path).st_mode) == 0o600
    assert browserless_session.load_session_file(path)["id"] == "test"
    os.chmod(path, 0o644)
    try:
        browserless_session.load_session_file(path)
    except PermissionError:
        pass
    else:
        raise AssertionError("insecure session file accepted")
PY
ok "provider host and bearer-file safety"

registry_files=("$skill_dir/references/provider-registry.local.example.md")
[[ -f "$skill_dir/references/provider-registry.local.md" ]] \
  && registry_files+=("$skill_dir/references/provider-registry.local.md")
python3 - "${registry_files[@]}" <<'PY'
import re
import sys

for filename in sys.argv[1:]:
    rows = []
    for line in open(filename, encoding="utf-8"):
        if not line.startswith("|") or "---" in line or "Priority" in line:
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) != 7:
            continue
        category, priority = cells[0], cells[1]
        if not re.fullmatch(r"[1-9][0-9]*", priority):
            raise AssertionError(f"{filename}: invalid priority {priority!r}")
        rows.append((category, int(priority)))
    if not rows:
        raise AssertionError(f"{filename}: no provider rows")
    if len(rows) != len(set(rows)):
        raise AssertionError(f"{filename}: duplicate priority within category")
PY
ok "explicit per-category provider priorities"

printf 'Results: %d passed, %d failed\n' "$pass" "$fail"
(( fail == 0 ))
