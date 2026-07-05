#!/usr/bin/env bash
set -u

# Lightweight provider reachability probe (transport-level).
# No API tokens required; 401/403 still count as "reachable".
#
# Usage:
#   ./scripts/check-provider-health.sh [anthropic openai google venice ollama]

TIMEOUT_SECONDS="${TIMEOUT_SECONDS:-5}"

declare -A URLS
URLS[anthropic]="https://api.anthropic.com"
URLS[openai]="https://api.openai.com/v1/models"
URLS[google]="https://generativelanguage.googleapis.com/"
URLS[venice]="https://api.venice.ai/api/v1/models"
URLS[ollama]="http://localhost:11434/api/tags"

if [ "$#" -gt 0 ]; then
  providers=("$@")
else
  providers=(anthropic openai google venice ollama)
fi

exit_code=0

probe() {
  local p="$1"
  local url="${URLS[$p]:-}"

  if [ -z "$url" ]; then
    echo "UNKNOWN $p (no probe configured)"
    exit_code=1
    return
  fi

  code=$(curl -sS -o /dev/null -w "%{http_code}" \
    --max-time "$TIMEOUT_SECONDS" \
    --connect-timeout "$TIMEOUT_SECONDS" \
    "$url" 2>/dev/null) || code="000"

  case "$code" in
    000)
      echo "DOWN     $p (no response in ${TIMEOUT_SECONDS}s)"
      exit_code=1
      ;;
    2*|3*|4*)
      echo "OK       $p ($code)"
      ;;
    5*)
      echo "DEGRADED $p ($code)"
      exit_code=1
      ;;
    *)
      echo "UNKNOWN  $p ($code)"
      exit_code=1
      ;;
  esac
}

for p in "${providers[@]}"; do
  probe "$p"
done

exit "$exit_code"
