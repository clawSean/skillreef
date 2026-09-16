#!/usr/bin/env bash
# Deep research via the high preset.
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
exec bash "$script_dir/agent.sh" high "$@"
