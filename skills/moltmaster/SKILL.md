---
name: moltmaster
description: >
  Use for OpenClaw OAuth profile refresh operations, Auth Molt, Moltmaster,
  Codex OAuth refresh, Claude or Anthropic OAuth profile refresh planning, or
  tasks involving OpenClaw auth profile inspection, pruning, or refresh without
  running openclaw doctor.
---

# Moltmaster

Controlled OpenClaw OAuth refresh via `scripts/moltmaster.mjs`. Wraps `resolveApiKeyForProfile` — no `openclaw doctor`, no blind mutations.

> ⚠️ **Auth engine broken since 2026-06-30:** OpenClaw migrated auth profiles into the per-agent sqlite store (`agents/<id>/agent/openclaw-agent.sqlite`, `auth_profile_store` table); `auth-profiles.json` is now a broken symlink, so any live `--dry-run`/`--execute` crashes with ENOENT. Rework pending: go through the plugin-SDK `ensureAuthProfileStore` instead of raw JSON reads. Offline tests still pass (temp fixtures).

## Moltmaster Pulse (live since 2026-07-03)

Minimal keep-warm pings for subscription provider rate windows. Entirely separate engine from auth refresh — deterministic bash, no LLM, no credential mutation.

> ⚠️ **2026-07-04 consolidation:** two Pulse engines were accidentally built in parallel on 2026-07-03 (a systemd timer + an OS-cron workspace copy), double-pinging every lane. Both legacy copies were **removed 2026-07-04** — the sole engine of record is **`~/.openclaw/extensions/moltmaster/core/pulse.sh`** (crontab `MOLTMASTER_PULSE`), published at github.com/clawSean/moltmaster. See the Pulse section below.

## Default stance

- **Dry-run by default.** Never run `--execute` unless the user explicitly asks for a live refresh.
- Never print raw token values. Fingerprints (12-char SHA-256 prefixes) only.
- Backup files contain credentials — treat them as sensitive. Do not copy to chat, logs, or shared storage.
- Only operate on providers verified to support refresh. Start with Codex. See `references/provider-expansion.md` before touching any other provider.
- Do not suggest OpenAI API-key Pulse lanes by default. They spend a tiny amount of API credit and do not warm subscription windows. As of 2026-07-09, live `openai-env` / `openai-cmd` lanes are commented out locally and the Pulse engine skips API-key lanes unless `PULSE_ALLOW_API_KEYS=1` is explicitly set.

## Usage

```sh
# Inspect (safe, no mutation)
node skills/moltmaster/scripts/moltmaster.mjs --dry-run
node skills/moltmaster/scripts/moltmaster.mjs --dry-run --profile openai-codex:claw3@edge.app

# Standard refresh (profile must be expired or within OpenClaw's ~5 min refresh margin)
node skills/moltmaster/scripts/moltmaster.mjs --execute --profile openai-codex:claw3@edge.app
node skills/moltmaster/scripts/moltmaster.mjs --execute --all

# Force-expire refresh (for usable-but-expiring profiles)
node skills/moltmaster/scripts/moltmaster.mjs --execute --force-expired-for-refresh --profile openai-codex:claw3@edge.app

# Prune old backup files
node skills/moltmaster/scripts/moltmaster.mjs --prune-backups --older-than 30
node skills/moltmaster/scripts/moltmaster.mjs --prune-backups --older-than 30 --execute
```

## Force-expired-for-refresh guardrails

Use this mode when a profile is expiring but not yet within OpenClaw's ~5-minute refresh window.

Requirements:
- `--execute` **and** exactly one `--profile` — no exceptions.
- Refuses `--all`.
- Refuses if same profile was refreshed within the last 60s (cooldown guard).
- Verifies post-refresh expiry exceeds original **and** at least one token fingerprint changed — rolls back on failure.

## Provider scope

**Codex only by default.** The script enforces an explicit Codex OAuth allowlist:
- `openai-codex:[^/\s]+@edge\.app`
- `openai-codex:you@example.com`

Before attempting any other provider, read `references/provider-expansion.md`. Do not attempt `--all` across providers blindly.

## Tests

```sh
node skills/moltmaster/scripts/moltmaster.test.mjs
```

Covers: dry-run, flag refusals (8 cases), profile validation, prune dry-run. Force-refresh success/rollback are manual-only (require live OpenClaw runtime and credentials).

## Environment overrides (testing only)

| Variable | Purpose |
|---|---|
| `AUTH_MOLT_SDK_PATH` / `MOLTMASTER_SDK_PATH` | Override OpenClaw plugin SDK runtime path |
| `AUTH_MOLT_STORE_PATH` | Override auth store path |
| `AUTH_MOLT_BACKUP_DIR` | Override backup directory |
| `AUTH_MOLT_STATE_FILE` | Override cooldown state file |

## Pulse (5h+5m window-warming pings) — LIVE 2026-07-03

> ⚠️ **Engine of record moved 2026-07-04:** the crontab MOLTMASTER_PULSE line now
> runs `~/.openclaw/extensions/moltmaster/core/pulse.sh` (generalized,
> shippable engine; same state dir `~/.openclaw/moltmaster/pulse/`, same
> kill switch `pulse.off`, lanes in `extensions/moltmaster/lanes.conf`).
> The legacy workspace copy (`scripts/pulse.sh` here) and the systemd copy were
> **removed 2026-07-04** per JPop; rollback source is the git history at
> github.com/clawSean/moltmaster. Lane changes go in the extension's lanes.conf.

The engine sends one tiny model turn per lane whenever that lane's last
ping is ≥5h05m old, so subscription 5-hour windows are already counting down
before real work starts. Runs from OS crontab (`MOLTMASTER_PULSE`, every 5 min,
flock-guarded) — the per-lane state gate means cron cadence ≠ ping volume.

- **Lanes (all-accounts since 2026-07-04, per JPop):**
  - Claude OAuth `personal`, `qa`, `clawdia`, `claw1`, `nick` (haiku ping via
    direct `claude -p`, tokens from `~/.openclaw/.env`; `nick` is on per
    JPop's "turn on all" — `PULSE_EXCLUDE_NICK=1` to opt out if Nick objects)
  - `store-default` — `anthropic:default` token read live from the OpenClaw
    sqlite auth store at ping time (survives gateway token refreshes)
  - `edgeclaw-work` — the native interactive `claude` login
    (**edgeclaw@edge.app**, work Team sub — the old claude-work lane). Runs
    `claude -p` with NO token override so the CLI auto-refreshes
    `~/.claude/.credentials.json` (override tokens 401 after expiry).
  - `openai-codex` — `openclaw infer model run --model openai/gpt-5.4-mini`;
    effective auth is `openai:you@example.com` OAuth (the warmable
    subscription).
  - `openai-key-main` + `openai-key-codexhome` — optional OpenAI API-key
    health-check lanes (.env/gateway sk-svcacct + <your-agent> codex-home
    sk-proj), pinged via direct `curl /v1/responses` (~16-token gpt-5.4-mini
    call). No 5h subscription window is warmed; these are alive-checks only.
    Standing direction from 2026-07-09: recurring API-key lanes stay off by
    default. The local `lanes.conf` entries are commented, and the live engine
    also skips `openai-env` / `openai-cmd` unless `PULSE_ALLOW_API_KEYS=1` is
    explicitly set. Prefer one-shot key-health checks when needed.
  - Caveat: `store-default`/`edgeclaw-work` token values are distinct from the
    env lanes, but OAuth rotation means they *might* map to the same underlying
    accounts — watch receipts for windows that always move together.
  - Do not delete `anthropic:default` casually: it is the credential backing
    `store-default`, and any direct Anthropic/OpenClaw-runtime model route can
    use it. As of 2026-07-09, normal default fallback uses
    `claude-cli/claude-opus-4-8`, but `anthropic/claude-opus-4-8` alias
    `opus-8` is still configured as a direct OpenClaw/Anthropic lane. To retire
    `anthropic:default`, first comment or retarget `store-default`, then remove
    or retarget direct `anthropic/*` routes that are not pinned to
    `agentRuntime.id: "claude-cli"`.
- **Never route pings through `claude-auth-router.sh`** — the router rotates
  profiles and notifies chats on limits; pings must be side-effect-free.
- **Kill switch:** `touch ~/.openclaw/moltmaster/pulse.off` (delete to resume).
- **Guards:** daily cap 6 pings/lane, 180s timeout, failed/limited pings still
  stamp the lane (no retry hammering).
- **State/log:** `~/.openclaw/moltmaster/pulse/` (`state/<lane>.last|.day`, `pulse.log`).
- The 5h-window-start hypothesis is still unproven per-lane; verify against
  `openclaw models status` (OpenAI meters) before trusting it for scheduling.
- 2026-07-09 fix: `core/pulse.sh` now explicitly exits `0` after processing a
  lanes file, so successful pings no longer look like shell failures because
  the final `read` hit EOF.

## Known breakage (2026-07-03)

- `scripts/moltmaster.mjs` (auth refresh) is **broken**: OpenClaw ≥2026.6.x
  migrated the auth store from `auth-profiles.json` to `openclaw-agent.sqlite`
  (2026-06-30 import); the JSON path is now a broken symlink. Needs a port
  before any refresh work.
- `~/scripts/claude-work.sh` execs the router with `--auth-profile work`,
  but `claude-profiles.json` has no `work` profile — the claude-work lane will
  error until a work profile is re-added. (2026-07-04: the work account itself
  was located — it's the native interactive `claude` login, edgeclaw@edge.app;
  Pulse now warms it via the `edgeclaw-work` lane. The router `work` profile is
  still missing for actual claude-work model routing.)

## Lab notebook

`projects/auth-health-cleanup/` is the origin lab notebook — RALPH_LOG.md has iteration history, claw3/claw4 trial notes, and force-expiry discovery. This skill is the canonical package; the project remains the lab notebook.
