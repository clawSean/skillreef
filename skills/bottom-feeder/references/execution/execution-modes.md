# execution-modes

Bottom Feeder supports three execution patterns. Pick the right one for your
run before you start — mixing modes mid-run is expensive and error-prone.

## 1) Single-agent (default)

**How it works:** One session handles topic selection, research, synthesis,
and writing sequentially.

**Use when:**
- Routine mode (1–2 topics)
- Stable, fast provider
- You want the simplest possible orchestration
- Total expected runtime < 30 minutes

**Tradeoffs:**
- ✅ Simple, reliable, easy to debug
- ✅ Zero subagent overhead
- ❌ Sequential — no parallelism
- ❌ If the session dies, you lose everything after the last written file

**Configuration:**
```yaml
execution_mode: single
```

## 2) Batched parallel

**How it works:** A coordinator spawns **N** short-lived subagents, each
assigned exactly **1 topic**. As subagents finish, the coordinator spawns
the next wave until all topics are complete.

**Use when:**
- Burn mode with 4+ topics
- Provider can sustain parallel load (check before launch)
- You want meaningful throughput gain without full orchestration complexity
- Total expected runtime 30 min – 2 hours

**Tradeoffs:**
- ✅ N× throughput when provider cooperates
- ✅ Isolated failures — one dead subagent doesn't kill the run
- ✅ Short-lived workers are more reliable than long-running ones
- ❌ Requires a batch-size limit, or you'll trigger rate-limit cascades
- ❌ Coordinator must track worker state

**Configuration:**
```yaml
execution_mode: batched
batch_size: 3                # concurrent subagents — keep small
subagent_timeout_seconds: 900
```

**Critical rule:** `batch_size` is a **cap**, not a target. Launching 8+
subagents simultaneously is the #1 cause of provider rate-limit cascades.
Stagger waves if you need more than `batch_size` topics.

## 3) Supervised

**How it works:** A coordinator orchestrates worker subagents and schedules
**checkpoint monitors** (cron or equivalent) that fire every N minutes to
verify progress, detect stalls, and alert on regressions. The coordinator
reads checkpoint output and decides whether to respawn failed topics.

**Use when:**
- Long burn runs (2+ hours)
- Unreliable providers or known cooldown windows
- You want push-based progress reports without polling
- Total expected runtime > 2 hours

**Tradeoffs:**
- ✅ Maximum resilience — stalls surface in minutes, not hours
- ✅ Push-based progress (no polling, no wasted tokens on status checks)
- ✅ Natural integration with provider fallback
- ❌ Most complex — requires cron/scheduler
- ❌ More moving parts to debug

**Configuration:**
```yaml
execution_mode: supervised
batch_size: 3
subagent_timeout_seconds: 1200
checkpoint_interval_minutes: 30
```

Pair with `references/execution/checkpoint-monitoring.md` for the cron
pattern and message templates.

## Decision cheat-sheet

| Signal                          | Mode       |
|---------------------------------|------------|
| 1–3 topics, routine             | single     |
| 4+ topics, burn, stable provider| batched    |
| Any run > 2h                    | supervised |
| Provider has known 429 patterns | supervised |
| You want to "fire and forget"   | supervised |
| You want minimum complexity     | single     |

## Anti-patterns (real-world failures that led to these rules)

1. **Spawning all topics at once** (e.g., 8 subagents immediately on a
   fresh session) → instant rate-limit cascade across every worker.
   **Fix:** respect `batch_size`, stagger waves.
2. **Long-running single subagent per topic batch** (e.g., 5-hour lifetime)
   → silent mid-run death from timeouts or provider cooldown.
   **Fix:** 1 topic per subagent, tight timeout (10–20 min).
3. **No checkpoints on long runs** → first sign of trouble is the final
   report showing 40% completion hours later.
   **Fix:** supervised mode with 30-min checkpoint crons.
4. **Provider lock with no fallback** → one cooldown window burns the
   whole run.
   **Fix:** configure `provider_fallback` in run-policy (see
   `references/execution/provider-fallback.md`).
