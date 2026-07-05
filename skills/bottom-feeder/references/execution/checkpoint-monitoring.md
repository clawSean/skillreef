# checkpoint-monitoring

Checkpoint monitors provide push-based progress during longer runs.

## When to use

- supervised runs
- burn runs > 60 minutes
- any run using subagents where silent failures are possible

## Pattern

Use one-shot checkpoints every 30 minutes (or configured interval):
- read run log (`knowledge/.runs/...`)
- find new files since run start/run-policy timestamp
- count files + lines
- compare disk state vs run-log state
- emit concise status (on pace / behind / stalled)

## Alert thresholds (suggested)

- 25% elapsed: alert only if 0 new files
- 50% elapsed: alert if <25% of target files
- 75% elapsed: alert if <50% of target files
- final checkpoint: alert if <80% of target files

## Important rule

Checkpoints are **read-only monitors**. They should not spawn workers. Coordinator handles recovery.

## Jitter

If many crons fire at the same minute, stagger heavy jobs by +2/+5/+8 min to reduce burst rate-limit cascades.
