#!/usr/bin/env bash
# Mock-provider harness health check. This does not compare real models.
set -euo pipefail

repo_root="${1:-${CLAWGAUGE_REPO_ROOT:-${MQB_REPO_ROOT:-$HOME/projects/openclaw}}}"
keep_root="${CLAWGAUGE_KEEP_QA_ROOT:-${MQB_KEEP_QA_ROOT:-0}}"
source_home="$HOME"
corepack_home="${COREPACK_HOME:-$source_home/.cache/node/corepack}"

if [[ ! -f "$repo_root/package.json" || ! -f "$repo_root/openclaw.mjs" ]]; then
  echo "ERROR: not an OpenClaw source checkout: $repo_root" >&2
  exit 2
fi
pnpm_path="$(command -v pnpm || true)"
if [[ -z "$pnpm_path" ]]; then
  echo "ERROR: pnpm is not available; ClawGauge will not install it" >&2
  exit 2
fi

safe_root="$(mktemp -d "${TMPDIR:-/tmp}/openclaw-clawgauge-preflight-XXXXXX")"
mkdir -p \
  "$safe_root/home" \
  "$safe_root/tmp" \
  "$safe_root/openclaw-home" \
  "$safe_root/state/credentials" \
  "$safe_root/xdg-config" \
  "$safe_root/xdg-data" \
  "$safe_root/xdg-cache"

cleanup() {
  if [[ "$keep_root" != "1" && -n "$safe_root" && -d "$safe_root" ]]; then
    case "$safe_root" in
      "${TMPDIR:-/tmp}"/openclaw-clawgauge-preflight-*) rm -rf -- "$safe_root" ;;
      *) echo "WARNING: refusing unexpected cleanup path: $safe_root" >&2 ;;
    esac
  fi
}
trap cleanup EXIT

echo "CLAWGAUGE_SAFE_ROOT=$safe_root"
echo "CLAWGAUGE_REPO_ROOT=$repo_root"
echo "CLAWGAUGE_KEEP_QA_ROOT=$keep_root"
echo "CLAWGAUGE_SIGNAL=harness-only"

(
  cd "$repo_root"
  clean_env=(
    env -i
    "PATH=${PATH:-/usr/bin:/bin}"
    "HOME=$safe_root/home"
    "TMPDIR=$safe_root/tmp"
    "OPENCLAW_ENABLE_PRIVATE_QA_CLI=1"
    "OPENCLAW_HOME=$safe_root/openclaw-home"
    "OPENCLAW_STATE_DIR=$safe_root/state"
    "OPENCLAW_CONFIG_PATH=$safe_root/openclaw.json"
    "OPENCLAW_OAUTH_DIR=$safe_root/state/credentials"
    "XDG_CONFIG_HOME=$safe_root/xdg-config"
    "XDG_DATA_HOME=$safe_root/xdg-data"
    "XDG_CACHE_HOME=$safe_root/xdg-cache"
    "OPENCLAW_SKIP_BROWSER_CONTROL_SERVER=1"
    "OPENCLAW_SKIP_GMAIL_WATCHER=1"
    "OPENCLAW_SKIP_CANVAS_HOST=1"
    "OPENCLAW_NO_RESPAWN=1"
    "COREPACK_ENABLE_NETWORK=0"
  )
  if [[ -d "$corepack_home" ]]; then
    clean_env+=("COREPACK_HOME=$corepack_home")
  fi
  if [[ -n "${LANG:-}" ]]; then
    clean_env+=("LANG=$LANG")
  fi
  if [[ -n "${LC_ALL:-}" ]]; then
    clean_env+=("LC_ALL=$LC_ALL")
  fi
  if [[ -n "${LC_CTYPE:-}" ]]; then
    clean_env+=("LC_CTYPE=$LC_CTYPE")
  fi
  "${clean_env[@]}" "$pnpm_path" openclaw qa suite \
    --provider-mode mock-openai \
    --concurrency 1 \
    --preflight
)

echo "CLAWGAUGE_STATE_FILES_BEGIN"
find "$safe_root" -maxdepth 5 -type f -print | sort | sed "s#^$safe_root#CLAWGAUGE_SAFE_ROOT#"
echo "CLAWGAUGE_STATE_FILES_END"
