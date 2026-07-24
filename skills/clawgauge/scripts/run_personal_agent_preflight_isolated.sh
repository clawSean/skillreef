#!/usr/bin/env bash
set -euo pipefail

repo_root="${1:-~/projects/openclaw}"
if [[ ! -d "$repo_root" ]]; then
  echo "OpenClaw repo root not found: $repo_root" >&2
  exit 2
fi
if [[ ! -f "$repo_root/package.json" ]]; then
  echo "OpenClaw repo root missing package.json: $repo_root" >&2
  exit 2
fi

safe_root="$(mktemp -d "${TMPDIR:-/tmp}/openclaw-mqb-qa-XXXXXX")"
mkdir -p \
  "$safe_root/home" \
  "$safe_root/state" \
  "$safe_root/xdg-config" \
  "$safe_root/xdg-data" \
  "$safe_root/xdg-cache"

cleanup() {
  if [[ "${MQB_KEEP_QA_ROOT:-0}" != "1" ]]; then
    rm -rf "$safe_root"
  fi
}
trap cleanup EXIT

echo "MQB_SAFE_ROOT=$safe_root"
echo "MQB_REPO_ROOT=$repo_root"
echo "MQB_KEEP_QA_ROOT=${MQB_KEEP_QA_ROOT:-0}"

(
  cd "$repo_root"
  OPENCLAW_ENABLE_PRIVATE_QA_CLI=1 \
  OPENCLAW_HOME="$safe_root/home" \
  OPENCLAW_STATE_DIR="$safe_root/state" \
  OPENCLAW_CONFIG_PATH="$safe_root/openclaw.json" \
  OPENCLAW_OAUTH_DIR="$safe_root/state/credentials" \
  XDG_CONFIG_HOME="$safe_root/xdg-config" \
  XDG_DATA_HOME="$safe_root/xdg-data" \
  XDG_CACHE_HOME="$safe_root/xdg-cache" \
  OPENCLAW_TEST_FAST=1 \
  OPENCLAW_SKIP_BROWSER_CONTROL_SERVER=1 \
  OPENCLAW_SKIP_GMAIL_WATCHER=1 \
  OPENCLAW_SKIP_CANVAS_HOST=1 \
  OPENCLAW_NO_RESPAWN=1 \
  pnpm openclaw qa suite \
    --provider-mode mock-openai \
    --pack personal-agent \
    --concurrency 1 \
    --preflight
)

echo "MQB_STATE_FILES_BEGIN"
find "$safe_root" -maxdepth 5 -type f | sort | sed "s#^$safe_root#MQB_SAFE_ROOT#"
echo "MQB_STATE_FILES_END"
