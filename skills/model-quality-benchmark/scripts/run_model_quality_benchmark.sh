#!/usr/bin/env bash
# Robust, isolated, scenario-by-scenario model-quality benchmark runner.
#
# Runs each requested model as the PRIMARY model against each requested QA
# scenario in its own isolated QA envelope, with a per-scenario wall-clock
# timeout so a single stall cannot eat the whole comparison. Every attempt
# either yields a real qa-suite-summary.json (copied into the run dir) or an
# explicit mqb-status.json sidecar labelled stalled/blocked. Feed the run dir
# to scripts/score_qa_suite.py for a scored GPT-vs-Claude report.
#
# Why scenario-by-scenario: a full `qa suite --pack personal-agent` run has
# stalled before writing final artifacts. Looping one scenario per gateway
# invocation, each under `timeout`, guarantees partial scored output with
# honest stalled/blocked labels even when one scenario hangs.
#
# Isolation: a fresh temp OPENCLAW_HOME/STATE/CONFIG/XDG root per invocation.
# No live Telegram/DM/state is touched; the Gateway is never restarted.
#
# Secrets: OpenAI auth is read from the codex-home auth.json via command
# substitution straight into OPENCLAW_LIVE_OPENAI_KEY. The value is never
# echoed and the file is never cat-ed.
#
# Config via env (all optional):
#   MQB_REPO_ROOT      OpenClaw source checkout      (default ~/projects/openclaw)
#   MQB_MODELS         primary models to test        (default "openai/gpt-5.5 claude-cli/claude-opus-4-8")
#   MQB_SCENARIOS      scenario ids; "preflight" =   (default "preflight personal-tool-safety-followthrough")
#                      the bootstrap preflight scenario
#   MQB_PROVIDER_MODE  mock-openai|aimock|live-frontier (default live-frontier)
#   MQB_TIMEOUT        per-scenario seconds          (default 240)
#   MQB_OUT            run output dir                (default skills/model-quality-benchmark/runs/run-<ts>)
#   MQB_CONCURRENCY    scenario worker concurrency   (default 1)
#   MQB_FAST           1 => pass --fast              (default 1)
#   MQB_ALT_MODE       strict|cross                  (default strict; strict => alt==primary, no fallback)
#   MQB_OPENAI_AUTH_JSON  codex-home auth.json       (default <your-agent> codex-home)
#   MQB_KEEP_QA_ROOT   1 => keep temp state roots    (default 0)
set -uo pipefail

REPO_ROOT="${MQB_REPO_ROOT:-~/projects/openclaw}"
MODELS_RAW="${MQB_MODELS:-openai/gpt-5.5 claude-cli/claude-opus-4-8}"
SCENARIOS_RAW="${MQB_SCENARIOS:-preflight personal-tool-safety-followthrough}"
PROVIDER_MODE="${MQB_PROVIDER_MODE:-live-frontier}"
TIMEOUT_S="${MQB_TIMEOUT:-240}"
CONCURRENCY="${MQB_CONCURRENCY:-1}"
FAST="${MQB_FAST:-1}"
ALT_MODE="${MQB_ALT_MODE:-strict}"
OPENAI_AUTH_JSON="${MQB_OPENAI_AUTH_JSON:-~/.openclaw/agents/<your-agent>/agent/codex-home/auth.json}"
KEEP_ROOT="${MQB_KEEP_QA_ROOT:-0}"
TS="$(date -u +%Y%m%dT%H%M%SZ)"
OUT="${MQB_OUT:-~/.openclaw/workspace/skills/model-quality-benchmark/runs/run-$TS}"

if [[ ! -f "$REPO_ROOT/package.json" || ! -f "$REPO_ROOT/openclaw.mjs" ]]; then
  echo "ERROR: not an OpenClaw source checkout: $REPO_ROOT" >&2
  exit 2
fi
if ! command -v timeout >/dev/null 2>&1; then
  echo "ERROR: coreutils 'timeout' is required" >&2
  exit 2
fi

# Normalise comma/space separated lists.
read -r -a MODELS <<<"${MODELS_RAW//,/ }"
read -r -a SCENARIOS <<<"${SCENARIOS_RAW//,/ }"

mkdir -p "$OUT"
MANIFEST="$OUT/run-manifest.tsv"
printf 'model\tscenario\tstatus\texit\twall_s\tsummary_path\n' >"$MANIFEST"

echo "MQB_RUN_DIR=$OUT"
echo "MQB_REPO_ROOT=$REPO_ROOT"
echo "MQB_PROVIDER_MODE=$PROVIDER_MODE"
echo "MQB_MODELS=${MODELS[*]}"
echo "MQB_SCENARIOS=${SCENARIOS[*]}"
echo "MQB_TIMEOUT=${TIMEOUT_S}s  MQB_ALT_MODE=$ALT_MODE  MQB_FAST=$FAST"
echo

safe() { printf '%s' "$1" | tr '/:.' '___'; }

# --- Transient catalog-blocker quarantine ------------------------------------
# The scenario catalog loads EVERY qa/scenarios/**.yaml. A single file the
# built dist parser rejects (e.g. ui/ux-matrix-evidence-dashboard.yaml with
# execution.kind: script) blocks ALL suite runs. We move such blockers aside
# for the duration of the run and ALWAYS restore them on exit, leaving the
# OpenClaw working tree exactly as found. Nothing in OpenClaw source is
# persistently modified.
QUAR_DIR="$OUT/.quarantine"
QUAR_LIST="$OUT/.quarantine/restore-list.txt"
restore_quarantine() {
  [[ -f "$QUAR_LIST" ]] || return 0
  while IFS= read -r rel; do
    [[ -z "$rel" ]] && continue
    if [[ -f "$QUAR_DIR/$rel" && ! -f "$REPO_ROOT/$rel" ]]; then
      mkdir -p "$REPO_ROOT/$(dirname "$rel")"
      mv "$QUAR_DIR/$rel" "$REPO_ROOT/$rel" && echo "restored: $rel"
    fi
  done <"$QUAR_LIST"
  : >"$QUAR_LIST"
}
trap restore_quarantine EXIT INT TERM

probe_catalog() { # prints the first blocker rel-path to stdout, or nothing if clean
  local proot; proot="$(mktemp -d "${TMPDIR:-/tmp}/openclaw-mqb-probe-XXXXXX")"
  local log="$proot/cov.log"
  OPENCLAW_ENABLE_PRIVATE_QA_CLI=1 OPENCLAW_HOME="$proot/home" OPENCLAW_STATE_DIR="$proot/state" \
    OPENCLAW_CONFIG_PATH="$proot/openclaw.json" XDG_CONFIG_HOME="$proot/xc" XDG_DATA_HOME="$proot/xd" \
    XDG_CACHE_HOME="$proot/xh" \
    timeout 90 node "$REPO_ROOT/openclaw.mjs" qa coverage --repo-root "$REPO_ROOT" --json >"$log" 2>&1
  local rc=$?
  if [[ $rc -ne 0 ]]; then
    grep -aoE '[A-Za-z0-9_./-]+\.ya?ml: scenario' "$log" 2>/dev/null | head -1 | sed 's/: scenario.*//'
  fi
  rm -rf "$proot"
}

quarantine_blockers() {
  mkdir -p "$QUAR_DIR"; : >"$QUAR_LIST"
  local i rel
  for i in $(seq 1 12); do
    rel="$(probe_catalog)"
    if [[ -z "$rel" ]]; then
      [[ $i -gt 1 ]] && echo "catalog clean after quarantining $((i-1)) file(s)"
      return 0
    fi
    if [[ ! -f "$REPO_ROOT/$rel" ]]; then
      echo "WARNING: catalog blocker '$rel' not a file; stopping quarantine" >&2
      return 1
    fi
    mkdir -p "$QUAR_DIR/$(dirname "$rel")"
    mv "$REPO_ROOT/$rel" "$QUAR_DIR/$rel"
    echo "$rel" >>"$QUAR_LIST"
    echo "quarantined catalog blocker: $rel"
  done
  echo "WARNING: still blocked after 12 quarantine passes" >&2
  return 1
}

echo "== probing scenario catalog =="
quarantine_blockers || echo "WARNING: catalog may still be blocked; runs may fail" >&2
echo

# Resolve OpenAI live key once, only if a model needs it. Value never printed.
OPENAI_KEY=""
needs_openai=0
for m in "${MODELS[@]}"; do
  [[ "$m" == openai/* || "$m" == codex/* ]] && needs_openai=1
done
if [[ "$needs_openai" == "1" && "$PROVIDER_MODE" == "live-frontier" ]]; then
  if [[ -n "${OPENCLAW_LIVE_OPENAI_KEY:-}" ]]; then
    OPENAI_KEY="$OPENCLAW_LIVE_OPENAI_KEY"
    echo "openai-auth: using preset OPENCLAW_LIVE_OPENAI_KEY"
  elif [[ -f "$OPENAI_AUTH_JSON" ]]; then
    # Command substitution: secret flows straight into the variable, never echoed.
    OPENAI_KEY="$(python3 -c 'import json,sys; print(json.load(open(sys.argv[1])).get("OPENAI_API_KEY",""))' "$OPENAI_AUTH_JSON" 2>/dev/null)"
    if [[ -n "$OPENAI_KEY" ]]; then
      echo "openai-auth: loaded key from codex-home auth.json (value not shown)"
    else
      echo "openai-auth: WARNING could not read OPENAI_API_KEY from auth.json" >&2
    fi
  else
    echo "openai-auth: WARNING no OPENCLAW_LIVE_OPENAI_KEY and no auth.json at $OPENAI_AUTH_JSON" >&2
  fi
fi

other_model() { # echo the first model that differs from $1, else $1
  local self="$1" m
  for m in "${MODELS[@]}"; do [[ "$m" != "$self" ]] && { printf '%s' "$m"; return; }; done
  printf '%s' "$self"
}

for model in "${MODELS[@]}"; do
  if [[ "$ALT_MODE" == "cross" ]]; then alt="$(other_model "$model")"; else alt="$model"; fi
  cli_auth_args=()
  [[ "$model" == claude-cli/* ]] && cli_auth_args=(--cli-auth-mode subscription)
  fast_args=()
  [[ "$FAST" == "1" ]] && fast_args=(--fast)

  for scenario in "${SCENARIOS[@]}"; do
    sc_out="$OUT/$(safe "$model")/$(safe "$scenario")"
    mkdir -p "$sc_out"
    run_log="$sc_out/run.log"

    # Preflight ignores --output-dir (writes to .artifacts/qa-e2e/preflight/).
    # Non-preflight REQUIRES --output-dir to be a relative path inside the repo
    # root, so we target a repo-relative .artifacts path and copy results out.
    scenario_args=()
    out_args=()
    rel_out=".artifacts/qa-e2e/mqb-$TS/$(safe "$model")/$(safe "$scenario")"
    if [[ "$scenario" == "preflight" || "$scenario" == "__preflight__" ]]; then
      scenario_args=(--preflight)
    else
      scenario_args=(--scenario "$scenario")
      out_args=(--output-dir "$rel_out")
    fi

    state_root="$(mktemp -d "${TMPDIR:-/tmp}/openclaw-mqb-live-XXXXXX")"
    mkdir -p "$state_root/home" "$state_root/state" "$state_root/xdg-config" "$state_root/xdg-data" "$state_root/xdg-cache"

    echo ">>> model=$model alt=$alt scenario=$scenario timeout=${TIMEOUT_S}s"
    echo "    state_root=$state_root  out=$sc_out"

    start=$(date +%s)
    qa_env=(
      OPENCLAW_ENABLE_PRIVATE_QA_CLI=1 \
      OPENCLAW_HOME="$state_root/home" \
      OPENCLAW_STATE_DIR="$state_root/state" \
      OPENCLAW_CONFIG_PATH="$state_root/openclaw.json" \
      OPENCLAW_OAUTH_DIR="$state_root/state/credentials" \
      XDG_CONFIG_HOME="$state_root/xdg-config" \
      XDG_DATA_HOME="$state_root/xdg-data" \
      XDG_CACHE_HOME="$state_root/xdg-cache" \
      OPENCLAW_TEST_FAST=1 \
      OPENCLAW_SKIP_BROWSER_CONTROL_SERVER=1 \
      OPENCLAW_SKIP_GMAIL_WATCHER=1 \
      OPENCLAW_SKIP_CANVAS_HOST=1 \
      OPENCLAW_NO_RESPAWN=1
    )
    [[ -n "$OPENAI_KEY" ]] && qa_env+=(OPENCLAW_LIVE_OPENAI_KEY="$OPENAI_KEY")

    # The whole pre-run summary set so we can detect what this run wrote.
    timeout -k 10 "$TIMEOUT_S" env \
      "${qa_env[@]}" \
      node "$REPO_ROOT/openclaw.mjs" qa suite \
        --repo-root "$REPO_ROOT" \
        --provider-mode "$PROVIDER_MODE" \
        --model "$model" \
        --alt-model "$alt" \
        --concurrency "$CONCURRENCY" \
        --allow-failures \
        "${fast_args[@]}" \
        "${cli_auth_args[@]}" \
        "${out_args[@]}" \
        "${scenario_args[@]}" \
        >"$run_log" 2>&1
    code=$?
    end=$(date +%s); wall=$((end - start))

    # Locate the summary this run wrote: prefer the path it printed, else the
    # newest qa-suite-summary.json under the out dir, else newest in .artifacts
    # created during this run window.
    summary_path="$(grep -aoE '/[^ ]*qa-suite-summary\.json' "$run_log" 2>/dev/null | tail -1)"
    if [[ -z "$summary_path" || ! -f "$summary_path" ]]; then
      summary_path="$(find "$REPO_ROOT/$rel_out" -name qa-suite-summary.json -newermt "@$start" 2>/dev/null | head -1)"
    fi
    if [[ -z "$summary_path" || ! -f "$summary_path" ]]; then
      summary_path="$(find "$sc_out" -name qa-suite-summary.json -newermt "@$start" 2>/dev/null | head -1)"
    fi
    if [[ -z "$summary_path" || ! -f "$summary_path" ]]; then
      summary_path="$(find "$REPO_ROOT/.artifacts" -name qa-suite-summary.json -newermt "@$start" 2>/dev/null | head -1)"
    fi

    if [[ -n "$summary_path" && -f "$summary_path" ]]; then
      # Copy the real artifacts into the run dir so scoring is single-rooted.
      cp -f "$summary_path" "$sc_out/qa-suite-summary.json" 2>/dev/null || true
      rpt="${summary_path%qa-suite-summary.json}qa-suite-report.md"
      [[ -f "$rpt" ]] && cp -f "$rpt" "$sc_out/qa-suite-report.md" 2>/dev/null || true
      status="ran(exit=$code)"
      rm -f "$sc_out/mqb-status.json"
    else
      if [[ "$code" == "124" || "$code" == "137" ]]; then label="stalled"; else label="blocked"; fi
      status="$label(exit=$code)"
      python3 - "$sc_out/mqb-status.json" "$model" "$scenario" "$code" "$wall" "$label" "$PROVIDER_MODE" "$alt" <<'PY'
import json, sys
out, model, scenario, code, wall, label, mode, alt = sys.argv[1:9]
json.dump({"model": model, "scenario": scenario, "exit_code": int(code),
           "wall_seconds": float(wall), "status_label": label,
           "provider_mode": mode, "alt_model": alt}, open(out, "w"), indent=2)
PY
      summary_path=""
    fi

    printf '%s\t%s\t%s\t%s\t%s\t%s\n' "$model" "$scenario" "$status" "$code" "$wall" "${summary_path:-none}" >>"$MANIFEST"
    echo "    -> $status  wall=${wall}s  summary=${summary_path:-NONE}"
    [[ "$KEEP_ROOT" != "1" ]] && rm -rf "$state_root"
    echo
  done
done

echo "==== run manifest ($MANIFEST) ===="
cat "$MANIFEST"
echo
echo "Score it with:"
echo "  python3 $(dirname "$0")/score_qa_suite.py --run-dir $OUT --out $OUT/score-report.md --json $OUT/scorecard.json"
