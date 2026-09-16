#!/usr/bin/env bash
# Multi-hop research via the medium preset.
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
exec bash "$script_dir/agent.sh" medium "$@"
