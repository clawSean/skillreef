#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
reconciler="$script_dir/reconcile-outbound.sh"
test_dir="$(mktemp -d)"
trap 'rm -rf "$test_dir"' EXIT

fake_cli="$test_dir/fake-imsg"

cat >"$fake_cli" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

[[ "${1:-}" == "history" ]]

printf '%s\n' \
  '{"id":1,"guid":"GUID-ONE","created_at":"2026-07-28T10:00:00.000Z","is_from_me":true,"text":"exact text","attachments":[]}' \
  '{"id":2,"guid":"GUID-INBOUND","created_at":"2026-07-28T10:01:00.000Z","is_from_me":false,"text":"exact text","attachments":[]}' \
  '{"id":3,"guid":"GUID-DUP-A","created_at":"2026-07-28T10:02:00.000Z","is_from_me":true,"text":"duplicate text","attachments":[]}' \
  '{"id":4,"guid":"GUID-DUP-B","created_at":"2026-07-28T10:03:00.000Z","is_from_me":true,"text":"duplicate text","attachments":[]}'
EOF
chmod 755 "$fake_cli"

exact_result="$(
  "$reconciler" --cli "$fake_cli" --chat-id 1 \
    --text "exact text" --since 2026-07-28T09:59:00.000Z
)"
jq -e '
  .status == "delivered"
  and .match.guid == "GUID-ONE"
' >/dev/null <<<"$exact_result"

set +e
not_found_result="$(
  "$reconciler" --cli "$fake_cli" --chat-id 1 \
    --guid GUID-MISSING --since 2026-07-28T09:59:00.000Z
)"
not_found_status=$?

ambiguous_result="$(
  "$reconciler" --cli "$fake_cli" --chat-id 1 \
    --text "duplicate text" --since 2026-07-28T09:59:00.000Z
)"
ambiguous_status=$?
set -e

[[ "$not_found_status" -eq 2 ]]
jq -e '.status == "not_found" and (.matches | length) == 0' \
  >/dev/null <<<"$not_found_result"

[[ "$ambiguous_status" -eq 3 ]]
jq -e '.status == "ambiguous" and (.matches | length) == 2' \
  >/dev/null <<<"$ambiguous_result"

printf 'reconcile-outbound tests passed\n'
