---
name: bottom-feeder
description: Knowledge research pipeline for OpenClaw. Selects topics (context-driven, seeds, knowledge gaps, or external signals), researches with all available tools, synthesizes durable notes, and writes/updates files in knowledge/topics and knowledge/research. Modes — routine (1-2 topics), burn (N topics), fleet (external topic list, parallel dispatch). Use when asked to build or refresh knowledge files, run a scheduled knowledge-crawl, detect knowledge gaps, or run budget-aware research passes. Provider-agnostic (Anthropic, OpenAI, Venice/Diem, etc.).
---

# Bottom Feeder

4-stage pipeline: select → collect → synthesize → write.
Depth over breadth. Write after every topic. Never batch.
Provider-agnostic — works with Anthropic, OpenAI, Venice/Diem, or local models.

## Inputs to Load First

1. `config/defaults.yaml`
2. `config/topics.md` — seed topic list
3. If present, `config/next-topic.md` — force-priority override
4. If present, `config/run-policy.md` — hard constraints for the current run (derive a fresh one from `config/run-policy.md.example`)
5. If present, `config/signals.yaml` — external signal sources like Asana/Jira/Linear/GitHub (see `references/topic-selection/external-signals.md`)

## Modes

### Routine (default)
- 1-2 topics, cost-conscious source usage, concise output, single-agent execution.
- Quiet completion unless the user asked for a report.

### Burn (explicit request)
- N topics, all available sources enabled, heavier model.
- Steps:
  1. Run `scripts/provider-usage.sh` (best-effort, continues on failure).
  2. Run `scripts/check-balance.sh` if you have balance JSON to parse (supports `remaining`, `balance`, `credits`, or `venice.data.diem`).
  3. Keep reserve from config: use `min_reserve_usd` when set (>0), otherwise fall back to legacy `min_reserve_diem`.
  4. Optional: run `scripts/check-provider-health.sh` to verify each provider in the fallback chain is reachable before launch.
  5. Execute in batched-parallel or supervised mode (see `references/execution/execution-modes.md`). Do **not** spawn all topics at once — that is the #1 cause of rate-limit cascades.
  6. Write after every topic (incremental write — never batch).
  7. Stop gracefully if balance or provider limit is hit.
  8. If a `provider_fallback` chain is declared, honor it strictly (see `references/execution/provider-fallback.md`).
  9. If multiple auth profiles are available, monitor for exhaustion and note when rotation is needed.
  10. Set cron safety nets per `references/output/burn-continuity.md`.
  11. After 80%+ complete, shift to strategic synthesis.

### Fleet (explicit request or topic list file provided)
- Accepts a topic list file path (markdown or plain text).
- Steps:
  1. Parse the topic list file. H2/H3 headings = topic names, body text under heading = context. Bullet items = topics, sub-bullets = context. Plain text: one topic per line. Extract topic name + any per-topic description.
  2. Run `scripts/provider-usage.sh` (best-effort, continues on failure).
  3. Create run progress log: `knowledge/.runs/<date>-fleet-<HHMM>.md`.
  4. Set cron safety nets per `references/output/burn-continuity.md`.
  5. Dispatch topics using the orchestrator pattern (below).
  6. Checkpoints at 25%, 50%, 75% or hourly — whichever comes first.
  7. After 80%+ complete, shift to strategic synthesis.
- **Orchestrator pattern:** the main session assigns topics, tracks completion, and reports. Each topic research is self-contained.
- **Parallelism preferred, not required.** When `sessions_spawn`, sub-agents, or similar tools are available, dispatch topics concurrently up to `parallelism` from config (and never more than `batch_size`). When unavailable (single-session, limited provider), process sequentially through the same pipeline. Never block or fail because parallelism is unavailable.
- **Sub-agent context:** each spawned sub-agent needs: (1) topic name + description from the list, (2) the knowledge-writer format spec from `references/output/knowledge-writer.md`, (3) the quality gate from `references/quality-gate/completion-checklist.md`, (4) output directory paths from config. Do not inject the full SKILL.md — keep prompts focused.
- **Sub-agent failure handling:** if a sub-agent dies, times out, or returns an error: log the topic as `status: failed` in the run progress log with the error reason, then continue with the next topic. Do not retry automatically — failed topics become follow-up candidates in the run summary. The orchestrator should never crash because a sub-agent failed.
- The orchestrator maintains the run progress log and writes strategic synthesis after all topics complete.

## Execution planning

Before selecting topics, decide **how** the run will execute (full decision guide in `references/execution/execution-modes.md`):

- **Single-agent (default):** one session writes all topics in sequence. Best for routine mode, ≤3 topics, stable providers.
- **Batched parallel:** N concurrent short-lived subagents (N=2–3 by default), 1 topic each, tight per-subagent timeout. Best for burn mode, >3 topics, when the provider can sustain parallelism.
- **Supervised:** coordinator + workers + checkpoint crons. Best for long runs (>2h), unreliable providers, or when you want push-based progress reports.

If a run-policy declares `execution_mode`, use it. Otherwise infer from `mode` (routine → single, burn → batched, explicit long run → supervised).

### Provider fallback (when configured)
If `config/run-policy.md` or `config/defaults.yaml` declares a `provider_fallback` chain, enforce it per `references/execution/provider-fallback.md`:
- Track consecutive failures per provider.
- On qualified failure (rate_limit / cooldown / auth / transport), rotate to the next provider.
- Log every rotation with reason, timestamp, and provider change in the run-progress file.
- If **all** providers in the chain are exhausted, stop and ask the user whether to wait, extend the chain, or abort.

### Provider lock (strict mode)
If `config/run-policy.md` specifies `provider_lock: <provider>` and **no** fallback chain, enforce the lock strictly and stop on failure. Do not silently switch providers. Use this only when provider compliance is a hard requirement (legal/billing/policy). Prefer fallback chains in normal operation.

## Pipeline

### Stage 1: Select topic

**Skip when topics are provided directly** (ad-hoc, burn with explicit list, fleet mode, or `config/next-topic.md`). Go straight to Stage 2.

When selection is needed:
1. `references/topic-selection/context-driven.md` — mine workspace context (PRIMARY)
2. `references/topic-selection/department-playbooks.md` — per-department guides
3. `references/topic-selection/hardcoded-list.md` — seed list + external file fallback
4. `references/topic-selection/external-signals.md` — optional: pull live task/issue/ticket signal from Asana/Jira/Linear/GitHub/Notion/etc. to steer topics toward real operational pressure

Combine candidates, dedupe, score by Urgency × Impact × Knowledge Gap, pick top N.

Before finalizing, check `knowledge/` for existing coverage. Strong + recent coverage → skip to next candidate.

### Stage 2: Collect research

Follow `references/research-sources.md`.

**Core principle: use ALL tools available in your current environment.** Do not default to a single search provider. Triangulate across source categories.

Before external searches, check local knowledge (`knowledge/`, `memory/`) for existing coverage.

Source strategy by topic type:
- **Operational/team topics:** internal tools first (Asana, Slack, Intercom), then web for best practices.
- **Technical/code topics:** clone repos, read source code, then web for docs and community context.
- **Market/competitive topics:** web search + structured APIs, then social for sentiment.
- **Strategic/synthesis topics:** local knowledge + internal tools, then web to validate.

**Cost awareness:** routine mode uses 1-2 search queries + local knowledge. Burn/fleet mode uses everything aggressively.

### Stage 3: Synthesize + quality gate

One durable, standalone knowledge artifact per topic:
- What it is
- Current state
- Why it matters (for the user's ecosystem/team/work)
- Key entities/projects
- Open questions + what to watch
- Sources with dates

For updates, prepend a "What's new" section. For department playbooks, follow `references/topic-selection/department-playbooks.md`.

**Quality gate:** run `references/quality-gate/completion-checklist.md` before advancing. Every section must pass or be tagged `[INCOMPLETE: reason]`.

**Checkpoints (burn/fleet):**
- After topic 5 (or 25% in fleet): offer user calibration review of 2-3 files.
- After topic 15 (or 50% in fleet): check context — if >60%, consider fresh session; if >70%, strongly prefer it.
- Hourly: `session_status` for context % and provider state.

### Stage 4: Write output

Use:
- `references/output/knowledge-writer.md` — file format
- `references/output/run-progress.md` — audit trail
- `references/output/lobsearch-index.md` — search index refresh (best-effort)
- `references/output/strategic-synthesis.md` — cross-topic action plans
- `references/output/burn-continuity.md` — cron safety nets for long runs

Write immediately after each topic clears the quality gate (incremental write — never batch all topics first).
Update the run progress log after every write: `knowledge/.runs/<date>-<mode>-<HHMM>.md`. This is your audit trail — always current, even if the run is interrupted.

### Stage 5: Monitoring (optional)

For **supervised** or long burn runs, schedule checkpoint jobs (cron or equivalent) to verify forward progress and surface stalls before they become expensive — see `references/execution/checkpoint-monitoring.md`. Checkpoints read the run-progress file and new-file diffs and announce status; they do **not** spawn new workers, they raise alerts the coordinator can act on. For recovery when subagents die or the run-log drifts from disk, see `references/execution/recovery-patterns.md`.

## Ad-hoc topic injection

"Run bottom feeder on [topic1, topic2, ...]"
- Skips Stage 1. No limit on topic count.
- Quality gate and progress logging still apply.

## Phased burn (team deployments)

**Phase 1 — Context gathering (15-30 min):** Mine workspace, score topics.
**Phase 2 — Topic burn (bulk):** Priority order. Checkpoints after 5 and 15.
**Phase 3 — Department playbooks (15-20%):** Per-department guides with live task data.
**Phase 4 — Strategic synthesis (10-15%):** Priority matrix, competitive positioning, action items. See `references/output/strategic-synthesis.md`.

## Guardrails

- Never spend down to zero unless the user explicitly says to.
- Skip duplicate rewrites when no meaningful updates exist.
- Prefer local/free sources before paid ones.
- Weak sources → write a partial with `[INCOMPLETE: reason]` tags and clear uncertainty notes.
- Split oversized output into follow-up research files; keep files readable.
- Log all sources used (tool, URL, date) in every output file.
- Link every synthesis recommendation to its supporting knowledge file.
- **Never spawn more than `batch_size` concurrent subagents** (default: 3). Larger parallel spawns trigger provider rate-limit cascades and kill throughput.
- **Keep subagents short-lived** (1 topic per subagent, tight timeout). Long-running subagents die silently under load.
- **Keep the run-log synced with disk state.** If a file exists but the run-log still shows "in-progress", the log is stale and must be reconciled (see `references/output/run-progress.md`).
- In burn mode with multiple auth profiles, track which profile is active and flag when switching is needed.

## Quick manual run recipe

1. Pick one topic from `config/topics.md`
2. Run brave search (3-6 results)
3. Synthesize into `knowledge/topics/<slug>.md`
4. Log run note in `memory/daily/YYYY-MM-DD.md`
5. Report: topic, files changed, estimated cost mode used

## Key references

- `references/execution/execution-modes.md` — single vs batched parallel vs supervised
- `references/execution/provider-fallback.md` — fallback chain semantics, triggers, rotation policy
- `references/execution/checkpoint-monitoring.md` — cron-based checkpoint pattern for long runs
- `references/execution/recovery-patterns.md` — what to do when subagents die
- `references/execution/lessons-learned.md` — retrospective from real burn runs
- `references/topic-selection/context-driven.md` — primary, context-mined topic selection
- `references/topic-selection/external-signals.md` — integrate live task/issue/ticket signal
- `references/research-sources.md` — unified source strategy
- `config/run-policy.md.example` — opt-in run-policy template with fallback + batching
- `config/signals.yaml.example` — opt-in external signal sources template
- `scripts/check-provider-health.sh` — pre-flight provider reachability probe

## Supervisor / tree-search mode (opt-in, re-introduced 2026-06-19)

For deep, broad, or high-uncertainty topics (or when `supervisor_mode: tree_search`
is set in `config/defaults.yaml` or the run policy), run the research as a bounded
supervisor instead of a single linear crawl:

1. Before collecting sources, follow `references/supervision/tree-search.md` —
   propose 3-5 candidate branches, score them, explore the best branch.
2. After synthesis and before the completion checklist, score the draft with
   `references/supervision/quality-score.md` (burn/deep pass threshold ≥10/12);
   retry once with a changed source mix / framing if the score is weak.
3. Log branch scores, retries, and the final quality score in the run-progress file.

Stays orthogonal to `execution_mode` (single/batched/supervised): tree-search controls
*research direction*; execution_mode controls *subagent orchestration*. They compose.
