#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage:
  reconcile-outbound.sh --chat-id ID (--text TEXT | --guid GUID)
    [--since ISO-8601] [--limit COUNT] [--cli PATH]

Exit codes:
  0  exactly one matching outbound message was found
  2  no matching outbound message was found
  3  multiple matching outbound messages were found
  64 invalid arguments

This is a read-only reconciliation helper. It never sends or retries.
EOF
}

chat_id=""
expected_text=""
expected_guid=""
since=""
limit="100"
cli_path="${IMESSAGE_CLI_PATH:-~/.openclaw/scripts/imsg-clawnode-ssh}"

while (($#)); do
  case "$1" in
    --chat-id)
      chat_id="${2:-}"
      shift 2
      ;;
    --text)
      expected_text="${2-}"
      shift 2
      ;;
    --guid)
      expected_guid="${2:-}"
      shift 2
      ;;
    --since)
      since="${2:-}"
      shift 2
      ;;
    --limit)
      limit="${2:-}"
      shift 2
      ;;
    --cli)
      cli_path="${2:-}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      usage >&2
      exit 64
      ;;
  esac
done

if [[ -z "$chat_id" ]] ||
  [[ -n "$expected_text" && -n "$expected_guid" ]] ||
  [[ -z "$expected_text" && -z "$expected_guid" ]]; then
  usage >&2
  exit 64
fi

if [[ ! "$limit" =~ ^[1-9][0-9]*$ ]]; then
  printf 'error: --limit must be a positive integer\n' >&2
  exit 64
fi

if [[ ! -x "$cli_path" ]]; then
  printf 'error: iMessage CLI wrapper is not executable: %s\n' "$cli_path" >&2
  exit 64
fi

history_file="$(mktemp)"
trap 'rm -f "$history_file"' EXIT

"$cli_path" history --chat-id "$chat_id" --limit "$limit" \
  --attachments --json >"$history_file"

matches="$(
  jq -s \
    --arg expected_text "$expected_text" \
    --arg expected_guid "$expected_guid" \
    --arg since "$since" \
    '
      map(
        select(.is_from_me == true)
        | select(
            ($since == "")
            or ((.created_at // "") >= $since)
          )
        | select(
            if $expected_guid != ""
            then ((.guid // "") == $expected_guid)
            else ((.text // "") == $expected_text)
            end
          )
        | {
            id,
            guid,
            created_at,
            text,
            attachment_count: ((.attachments // []) | length)
          }
      )
    ' "$history_file"
)"

match_count="$(jq 'length' <<<"$matches")"

case "$match_count" in
  0)
    jq -n \
      --arg status "not_found" \
      --arg chat_id "$chat_id" \
      --arg since "$since" \
      '{status: $status, chat_id: $chat_id, since: $since, matches: []}'
    exit 2
    ;;
  1)
    jq \
      --arg status "delivered" \
      '{status: $status, match: .[0]}' <<<"$matches"
    exit 0
    ;;
  *)
    jq \
      --arg status "ambiguous" \
      '{status: $status, matches: .}' <<<"$matches"
    exit 3
    ;;
esac
