# burn-continuity

Strategies for maintaining burn and fleet sessions across context limits and interruptions.

## The Problem

Extended sessions (4+ hours, or fleet runs with many topics) face three threats:
1. **Context overflow** -- session hits token limit, compaction loses progress tracking
2. **Session death** -- connection drops, process killed, provider rate limit
3. **Quality degradation** -- later topics get thinner as context fills with earlier output

## Solution: Cron Safety Nets

Set one-shot cron jobs at regular intervals (30-60 min) that:
- Check progress (read run log)
- Continue writing remaining topics if main session died
- Send progress updates to the user
- Self-delete after running (`--delete-after-run`)

```bash
openclaw cron add \
  --name "burn-check-HHMM" \
  --at "2026-04-04T15:00:00Z" \
  --channel <your-channel> --to <your-chat-id> \
  --model <cheaper-model> \
  --timeout-seconds 300 \
  --delete-after-run \
  --message "Continue the knowledge burn. Read <run-log>. Write remaining topics."
```

**Key design choices:**
- Use a cheaper model than the main session for cron continuity (saves budget)
- Set `--delete-after-run` so crons don't accumulate
- Include the full run log path in the message so the cron session has context
- Adjust `--channel` and `--to` for your deployment (Telegram, Slack, Discord, etc.)

## Solution: Run Progress Log

Always maintain `knowledge/.runs/<date>-<mode>-<HHMM>.md` with:
- Every topic completed (title, file path, time, sources used, confidence)
- Current status ("Continuing burn — 24 topics done, moving to Tier 3")
- Remaining topics list

This is the handoff document between sessions. If the main session dies and a cron picks up, it reads the log and continues where the last session left off.

## Solution: Quality Checkpoints

Combat quality degradation with explicit pause points:

- **After topic 5:** Pause. Ask the user to review 2-3 files. Calibrate.
- **After topic 15:** Check context usage. If >60%, consider starting a new session.
- **Every hour:** Run `session_status` to monitor context % and provider profile.

If context exceeds 70%, consider:
1. Starting a fresh session for remaining topics
2. Reducing source depth (fewer search queries per topic)
3. Writing shorter synthesis sections (focus on recommendations, skip background)

## Solution: Parallel Sub-Agents

For maximum throughput, spawn sub-agents per topic:

```
Main session: orchestrator
├── Sub-agent 1: researching Topic A → writes to knowledge/topics/a.md
├── Sub-agent 2: researching Topic B → writes to knowledge/topics/b.md
└── Sub-agent 3: researching Topic C → writes to knowledge/topics/c.md
```

Main session monitors progress and assigns next topic when a sub-agent finishes.

**Caution:** Sub-agents don't share context. Each one needs the relevant workspace context (team data, project management data) injected via the task prompt. Keep sub-agent tasks self-contained.

## Solution: Profile Rotation (Multi-Profile Setups)

If your provider has multiple API keys or team seats:
1. Check `session_status` every 30 min
2. Track token usage per profile
3. When approaching limits, switch to next profile
4. Log which profile was used for which topics (audit trail)

## Anti-Patterns

- ❌ Running for 8+ hours in a single session without context checks
- ❌ No run log (if session dies, all progress tracking is lost)
- ❌ Crons without self-delete (accumulate and fire repeatedly)
- ❌ Prioritizing topic count over topic quality in late sessions
- ❌ No user checkpoint (quality drifts without human calibration)
