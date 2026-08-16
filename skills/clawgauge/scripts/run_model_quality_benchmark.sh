#!/usr/bin/env bash
# Compatibility entry point. The Python runner supplies portable process-group
# timeouts on macOS and Linux and retains the old MQB_* environment aliases.
set -euo pipefail
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/run_openclaw_qa_gate.py" "$@"
