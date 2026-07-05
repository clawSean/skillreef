# lessons-learned

This file records operational lessons from real Bottom Feeder burn runs.

## Lesson: strict provider lock can waste entire windows

A long run with provider lock and no fallback hit sustained Anthropic 429 cooldown and stalled output for hours.

**Change:** add fallback chain + rotation triggers.

## Lesson: launching all subagents at once causes cascades

Parallel waves of 8+ workers can trigger immediate 429 failures across every worker.

**Change:** enforce batch-size caps and staggered waves.

## Lesson: short-lived workers outperform long-lived workers

Long-lived workers fail silently under load more often than one-topic workers.

**Change:** 1 topic per worker + tight timeout (10–20 min).

## Lesson: checkpoints catch issues early

30-minute checkpoint monitors dramatically improved recovery speed and accountability.

**Change:** add checkpoint-monitoring reference and supervised mode guidance.

## Lesson: external task systems improve topic relevance

Pulling live Asana/task data surfaced high-value operational themes not present in static seed lists.

**Change:** add external-signals module and config template.

## Lesson: run-log bookkeeping drifts under concurrency

Some completed files were not marked complete in logs.

**Change:** formal drift-reconciliation rules + stronger run-progress template.
