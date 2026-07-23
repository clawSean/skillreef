# Live Run Index

This index migrates the useful current run evidence from the staging project into the skill package.

## Representative Examples

- `examples/runs/gpt55-vs-xai-grok43/score-report.md`
- `examples/runs/gpt55-vs-xai-grok43/scorecard.json`

## Migrated Staging Artifacts

The following staging artifacts were moved into this skill under
`runs/legacy-20260621-staging-runs/`:

- `runs/legacy-20260621-staging-runs/2026-06-21-gpt55-vs-opus46.md`
- `runs/legacy-20260621-staging-runs/run-gpt55-vs-opus48-completed-score.md`
- `runs/legacy-20260621-staging-runs/run-gpt55-vs-xai-grok43/`

The old `~/projects/model-quality-benchmark-runs` path is now a
compatibility symlink to `runs/legacy-20260621-staging-runs/` so older chat and
memory links still resolve without making `~/projects` a second source of
truth.

New runs default to `skills/model-quality-benchmark/runs/<run-id>/`.
