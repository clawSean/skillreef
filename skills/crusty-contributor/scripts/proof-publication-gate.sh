#!/usr/bin/env bash
set -euo pipefail

state="${1:-}"
intent="${2:-}"
proof_required_before_publication="${3:-no}"

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

case "$proof_required_before_publication" in
  no|yes) ;;
  *)
    echo "proof-required-before-publication must be no or yes" >&2
    exit 64
    ;;
esac

if [[ "$state" == "satisfied" || "$state" == "not_required" ]]; then
  echo "ready_non_draft"
  exit 0
fi

if [[ "$proof_required_before_publication" == "yes" ]]; then
  echo "proof_blocked"
  exit 1
fi

if [[ "$intent" == "draft" ]]; then
  echo "draft_with_proof_debt"
  exit 0
fi

echo "ready_non_draft_with_proof_debt"
