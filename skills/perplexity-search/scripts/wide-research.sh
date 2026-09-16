#!/usr/bin/env bash
# Large evidence-backed collections via the wide-research preset.
set -euo pipefail
script_dir="$(cd "$(dirname "$0")" && pwd)"
exec bash "$script_dir/agent.sh" wide-research "$@"
