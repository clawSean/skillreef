#!/usr/bin/env bash
set -euo pipefail

state="${1:-}"
intent="${2:-}"
coordination_exception="${3:-no}"

case "$state" in
  not_required|planned|attempted|satisfied|blocked_external|stale) ;;
  *)
    echo "invalid proof state: ${state:-<empty>}" >&2
    exit 64
    ;;
esac

case "$intent" in
  non-draft|draft) ;;
  *)
    echo "invalid publication intent: ${intent:-<empty>}" >&2
    exit 64
    ;;
esac

case "$coordination_exception" in
  no|yes) ;;
  *)
    echo "coordination exception must be no or yes" >&2
    exit 64
    ;;
esac

if [[ "$state" == "satisfied" || "$state" == "not_required" ]]; then
  echo "ready_non_draft"
  exit 0
fi

if [[ "$intent" == "draft" && "$coordination_exception" == "yes" ]]; then
  echo "draft_coordination_only"
  exit 0
fi

echo "hold_local"
exit 1
