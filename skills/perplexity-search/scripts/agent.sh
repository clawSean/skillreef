#!/usr/bin/env bash
# Shared Perplexity Agent API runner.
# Usage: bash agent.sh <low|medium|high|wide-research|xhigh> "question"
# Optional named local profile: PERPLEXITY_KEY_PROFILE=fallback bash agent.sh high "question"

set -euo pipefail

if (( $# < 2 )); then
  echo "Usage: bash agent.sh <low|medium|high|wide-research|xhigh> \"question\"" >&2
  exit 64
fi

preset="$1"
shift
query="$*"

case "$preset" in
  low|medium|high|wide-research|xhigh) ;;
  *)
    echo "Invalid preset: $preset (expected low, medium, high, wide-research, or xhigh)" >&2
    exit 64
    ;;
esac

key_profile="${PERPLEXITY_KEY_PROFILE:-default}"
script_dir="$(cd "$(dirname "$0")" && pwd)"
local_credentials="$script_dir/../references/credentials.local.sh"

if [[ -z "${PERPLEXITY_API_KEY:-}" && -z "${PERPLEXITY_1PASSWORD_REF:-}" && -f "$local_credentials" ]]; then
  # shellcheck disable=SC1090
  source "$local_credentials"
fi

if [[ -z "${OP_SERVICE_ACCOUNT_TOKEN:-}" && -f "$HOME/.openclaw/.env" ]]; then
  set -a
  # shellcheck disable=SC1091
  source "$HOME/.openclaw/.env"
  set +a
fi

if [[ -n "${PERPLEXITY_API_KEY:-}" ]]; then
  api_key="$PERPLEXITY_API_KEY"
elif [[ -n "${PERPLEXITY_1PASSWORD_REF:-}" ]]; then
  api_key="$(op read "$PERPLEXITY_1PASSWORD_REF" 2>/dev/null)" || {
    echo "Failed to read Perplexity key profile '$key_profile' from 1Password" >&2
    exit 1
  }
else
  echo "No Perplexity credential route configured; set PERPLEXITY_API_KEY or PERPLEXITY_1PASSWORD_REF" >&2
  exit 1
fi

research_input="Research the question below. Lead with the direct answer. Prefer primary and authoritative sources where practical. Distinguish sourced facts from inference and uncertainty. Use inline citations and return a compact source-backed synthesis without filler.

Question:
$query"

payload="$(jq -n \
  --arg preset "$preset" \
  --arg input "$research_input" \
  '{preset: $preset, input: $input}')"

response_file="$(mktemp)"
trap 'rm -f "$response_file"; unset api_key' EXIT

set +e
http_code="$(curl -sS \
  --connect-timeout 15 \
  --max-time 900 \
  -o "$response_file" \
  -w '%{http_code}' \
  -X POST 'https://api.perplexity.ai/v1/agent' \
  -H "Authorization: Bearer $api_key" \
  -H 'Content-Type: application/json' \
  --data-binary "$payload")"
curl_status=$?
set -e
unset api_key

if (( curl_status != 0 )); then
  echo "Perplexity request failed (curl exit $curl_status)" >&2
  exit 1
fi

if [[ "$http_code" != "200" ]]; then
  message="$(jq -r '.error.message // .message // "request failed"' "$response_file" 2>/dev/null || true)"
  case "$http_code" in
    401) echo "Perplexity key '$key_profile' is invalid or expired" >&2 ;;
    402) echo "Perplexity key '$key_profile' is out of credits" >&2 ;;
    429) echo "Perplexity is rate limiting this request" >&2 ;;
    *) echo "Perplexity HTTP $http_code: $message" >&2 ;;
  esac
  exit 1
fi

status="$(jq -r '.status // "completed"' "$response_file")"
if [[ "$status" != "completed" ]]; then
  message="$(jq -r '.error.message // .incomplete_details.reason // "no provider detail"' "$response_file")"
  echo "Perplexity run ended with status '$status': $message" >&2
  exit 1
fi

answer="$(jq -r '
  .output_text //
  ([.output[]?
    | select(.type == "message")
    | .content[]?
    | select(.type == "output_text")
    | .text] | join("\n"))
' "$response_file")"

if [[ -z "$answer" || "$answer" == "null" ]]; then
  echo "Perplexity returned no final answer" >&2
  exit 1
fi

printf '%s\n' "$answer"

citation_ids="$(jq -Rn --arg text "$answer" \
  '[$text | scan("\\[(?:web:)?([0-9]+)\\]") | .[0]] | unique')"

sources="$(jq -r --argjson cited "$citation_ids" '
  [.output[]?
    | select(.type == "search_results")
    | .results[]?]
  | unique_by(.url)
  | if ($cited | length) > 0 then
      map(select((.id | tostring) as $id | ($cited | index($id)) != null))
    else
      .[:8]
    end
  | to_entries[]
  | "[\(.value.id // (.key + 1))] \(.value.title // "Untitled") — \(.value.url // "")"
' "$response_file")"

if [[ -n "$sources" ]]; then
  printf '\nSources:\n%s\n' "$sources"
else
  printf '\nSources: none returned by this run\n'
fi
