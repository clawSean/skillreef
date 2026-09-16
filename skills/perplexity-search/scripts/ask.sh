#!/usr/bin/env bash
# Everyday cited research via the low preset.
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
exec bash "$script_dir/agent.sh" low "$@"
