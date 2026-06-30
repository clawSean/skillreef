---
name: moltmaster
description: Moltmaster workflow for refreshing OpenClaw provider profiles safely.
---

# Moltmaster

Controlled OpenClaw OAuth refresh via `scripts/moltmaster.mjs`. Wraps `resolveApiKeyForProfile` — no `openclaw doctor`, no blind mutations.

## Default stance

- **Dry-run by default.** Never run `--execute` unless the user explicitly asks for a live refresh.
- Never print raw token values. Fingerprints (12-char SHA-256 prefixes) only.
- Backup files contain credentials — treat them as sensitive. Do not copy to chat, logs, or shared storage.
- Only operate on providers verified to support refresh. Start with Codex. See `references/provider-expansion.md` before touching any other provider.

## Usage

```sh
# Inspect (safe, no mutation)
node skills/moltmaster/scripts/moltmaster.mjs --dry-run
node skills/moltmaster/scripts/moltmaster.mjs --dry-run --profile openai-codex:you@example.com

# Standard refresh (profile must be expired or within OpenClaw's ~5 min refresh margin)
node skills/moltmaster/scripts/moltmaster.mjs --execute --profile openai-codex:you@example.com
node skills/moltmaster/scripts/moltmaster.mjs --execute --all

# Force-expire refresh (for usable-but-expiring profiles)
node skills/moltmaster/scripts/moltmaster.mjs --execute --force-expired-for-refresh --profile openai-codex:you@example.com

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

**Codex only by default.** The script enforces an `openai-codex:<profile-email>` allowlist. Set `AUTH_MOLT_ALLOWED_EMAIL_DOMAIN=example.com` to restrict refreshes to one domain.

Before attempting any other provider, read `references/provider-expansion.md`. Do not attempt `--all` across providers blindly.

## Tests

```sh
node skills/moltmaster/scripts/moltmaster.test.mjs
```

Covers: dry-run, flag refusals (8 cases), profile validation, prune dry-run. Force-refresh success/rollback are manual-only (require live OpenClaw runtime and credentials).

## Environment overrides (testing only)

| Variable | Purpose |
|---|---|
| `AUTH_MOLT_STORE_PATH` | Override auth store path |
| `AUTH_MOLT_BACKUP_DIR` | Override backup directory |
| `AUTH_MOLT_STATE_FILE` | Override cooldown state file |
| `AUTH_MOLT_ALLOWED_EMAIL_DOMAIN` | Optional email-domain allowlist, e.g. `example.com` |
| `AUTH_MOLT_SDK_PATH` | Override OpenClaw agent-runtime SDK import path |

## Notes

Keep environment-specific lab notes, real profile IDs, and auth-store backups outside the skill package. This skill should contain reusable procedure and code only.
