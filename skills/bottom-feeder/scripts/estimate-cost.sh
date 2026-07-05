#!/usr/bin/env bash
# Rough cost estimate by mode and source count.
# Returns a relative cost unit (not tied to any specific provider currency).
# Routine ~0.08 base, Burn ~0.60 base, +0.03 per additional source.
# Design: prints a number on success, prints "0.0000" on any error.
#         NEVER exits non-zero. Budget is informational only.
mode="${1:-routine}"
sources="${2:-2}"

case "$mode" in
  routine) base=0.08 ;;
  burn)    base=0.60 ;;
  fleet)   base=0.60 ;;  # fleet uses aggressive sources like burn
  *)       base=0.08 ;;  # unknown mode defaults to routine cost
esac

extra=$(awk -v s="$sources" 'BEGIN { v=(s>1)?(s-1)*0.03:0; printf "%.4f", v }' 2>/dev/null || echo "0.0000")
awk -v b="$base" -v e="$extra" 'BEGIN { printf "%.4f\n", b+e }' 2>/dev/null || echo "0.0000"
