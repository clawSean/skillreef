#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."

pass=0
fail=0

check() {
  local name="$1"
  shift
  if "$@" >/tmp/web-use-test.out 2>/tmp/web-use-test.err; then
    printf 'ok - %s\n' "$name"
    pass=$((pass + 1))
  else
    printf 'not ok - %s\n' "$name"
    sed 's/^/  /' /tmp/web-use-test.err
    fail=$((fail + 1))
  fi
}

echo "=== web-use skill baseline tests ==="

check "Frontmatter name matches directory name" grep -Eq '^name:[[:space:]]*"?web-use"?[[:space:]]*$' SKILL.md
check "browserless_extract helper parses" python3 -m py_compile scripts/browserless_extract.py
check "browserless_extract help works without credentials" python3 scripts/browserless_extract.py --help
check "browserless_extract help mentions retry option" bash -c 'python3 scripts/browserless_extract.py --help | grep -q -- "--max-retries"'
check "browserless_extract help mentions media limit option" bash -c 'python3 scripts/browserless_extract.py --help | grep -q -- "--media-limit"'
check "browserless_session helper parses" python3 -m py_compile scripts/browserless_session.py
check "browserless_session help works without credentials" python3 scripts/browserless_session.py --help
check "browserless_media_requests helper parses" python3 -m py_compile scripts/browserless_media_requests.py
check "browserless_media_requests help works without credentials" python3 scripts/browserless_media_requests.py --help
check "tinyfish helper parses" python3 -m py_compile scripts/tinyfish_browser_extract.py
check "tinyfish help works without optional deps" python3 scripts/tinyfish_browser_extract.py --help

rm -f /tmp/web-use-test.out /tmp/web-use-test.err

echo "Passed: $pass"
echo "Failed: $fail"

if [ "$fail" -ne 0 ]; then
  exit 1
fi
