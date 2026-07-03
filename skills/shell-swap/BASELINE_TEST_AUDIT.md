# Baseline Test Audit — shell-swap

## What exists

`scripts/test.sh` — 16 offline assertions covering:

1. **SKILL.md structure** — file exists, has YAML frontmatter with `name` and `description`
2. **Script validity** — `switch.sh` exists and passes `bash -n` syntax check
3. **Unknown alias rejection** — script exits non-zero for invalid model alias
4. **Dry-run correctness** — with temp fixture files: exits 0, prints target, reports "No files modified", leaves config files unchanged
5. **Live run correctness** — with temp fixture files: updates `openclaw.json` primary model, updates `sessions.json` model fields, updates `cron/jobs.json` payload model, creates `.bak` backups for both sessions and cron files

## How to run

```bash
bash scripts/test.sh
```

## Last run

- **Date:** 2026-05-09
- **Result:** 16/16 passed, 0 failed
- **Environment:** Linux, bash, python3

## Remaining gaps

- No test for `modelOverride` rewrite (fixture sessions lack a distinct override value)
- No test for `gpt-*` / `spark` / `codex` aliases (only `haiku` tested end-to-end)
- No test for missing config files (e.g. `openclaw.json` absent)
- No idempotency test (running same alias twice)
