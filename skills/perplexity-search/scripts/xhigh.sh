#!/usr/bin/env bash
# Explicit maximum-effort research via the xhigh preset.
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
exec bash "$script_dir/agent.sh" xhigh "$@"
