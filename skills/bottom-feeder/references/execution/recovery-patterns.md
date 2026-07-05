# recovery-patterns

How to recover safely when a run degrades.

## 1) Subagent failed before writing output

1. Mark topic as failed/incomplete in run log.
2. Respawn **one** worker for that topic.
3. If it fails twice, write a partial with `[INCOMPLETE: reason]` and continue.

## 2) Parallel launch triggered provider 429 cascade

1. Stop spawning new workers.
2. Rotate provider using fallback chain.
3. Relaunch in smaller batches (2–3 max).
4. Log incident details in run log.

## 3) Disk vs run-log drift

If files exist but run log still says spawned/in-progress:
- reconcile log to match disk
- add reconciliation note

If log says complete but file missing:
- downgrade status to failed
- respawn or mark follow-up

## 4) All providers exhausted

Stop gracefully and ask user whether to:
- wait and retry
- extend fallback chain
- abort

## Golden rules

- Disk is source of truth for file existence.
- Retry 1:1 (one failed topic → one respawn), not full-wave relaunch.
- Log all retries/rotations.
- Graceful stop is better than fake completion.
