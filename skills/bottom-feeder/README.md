# 🦞 Bottom Feeder

**A knowledge research pipeline skill for OpenClaw** that researches topics using all available tools and writes durable knowledge files.

Small sips by default. Fleet mode when you need scale. 🌊

Provider-agnostic — works with Anthropic, OpenAI, Venice/Diem, or whatever you're running. No vendor lock-in.

---

## What it does

A practical pipeline:

1. **Execution planning** — single / batched / supervised (how the run physically executes)
2. **Topic selection** — context-driven (your projects, people, decisions), seed lists, knowledge gaps, or optional external signals
3. **Research collection** — uses ALL available tools: web search, page fetching, local knowledge, internal tools (Asana, Slack, etc.), code repos, APIs, social, MCP tools
4. **Synthesis** — durable, actionable, self-contained markdown with quality gates
5. **Output writing + run logging** — to `knowledge/topics/` or `knowledge/research/`, with an audit trail in `knowledge/.runs/`
6. **Checkpoint monitoring** — for long runs

---

## Modes

| Mode | Topics | Sources | Parallelism |
|------|--------|---------|-------------|
| **Routine** (default) | 1-2 | Cost-conscious | Sequential |
| **Burn** | N (explicit) | All available | Sequential or batched |
| **Fleet** | External list | All available | Preferred when available |

**Fleet mode** accepts a topic list file (markdown or plain text), dispatches topics via sub-agents when available, falls back to serial when not. The orchestrator assigns, tracks, and reports.

**Execution modes** are orthogonal to research mode: `single` (one session), `batched` (N short-lived subagents), `supervised` (coordinator + workers + checkpoint crons for long runs).

---

## Folder structure

```text
skills/bottom-feeder/
├── SKILL.md                          ← main instruction file
├── config/
│   ├── defaults.yaml                 ← modes, budget, execution, sources, paths
│   ├── topics.md                     ← seed topic list
│   ├── run-policy.md.example         ← optional run-policy template
│   └── signals.yaml.example          ← optional external-signal template
├── references/
│   ├── research-sources.md           ← unified source strategy
│   ├── execution/
│   │   ├── execution-modes.md        ← single / batched / supervised
│   │   ├── provider-fallback.md      ← fallback chains + triggers
│   │   ├── checkpoint-monitoring.md  ← long-run checkpoints
│   │   ├── recovery-patterns.md      ← subagent failure / drift recovery
│   │   └── lessons-learned.md        ← production lessons
│   ├── topic-selection/
│   │   ├── context-driven.md         ← PRIMARY selection method
│   │   ├── department-playbooks.md   ← per-team operational guides
│   │   ├── hardcoded-list.md         ← seed list + external file support
│   │   └── external-signals.md       ← Asana/Jira/Linear/GitHub/Notion signals
│   ├── quality-gate/
│   │   └── completion-checklist.md   ← must-pass before next topic
│   └── output/
│       ├── knowledge-writer.md       ← file format spec
│       ├── run-progress.md           ← audit trail format
│       ├── strategic-synthesis.md    ← cross-topic action plans
│       ├── burn-continuity.md        ← cron safety nets, long runs
│       └── lobsearch-index.md        ← search index refresh
└── scripts/
    ├── provider-usage.sh             ← best-effort budget probe
    ├── check-balance.sh              ← balance extraction (never fails)
    ├── estimate-cost.sh              ← rough cost estimate (never fails)
    └── check-provider-health.sh      ← provider reachability preflight
```

Output goes to:
- `knowledge/topics/` — research files
- `knowledge/research/` — deep dives
- `knowledge/.runs/` — audit trail

---

## Quick start

1. Copy this folder into `workspace/skills/bottom-feeder`
2. Customize `config/topics.md` or let context-driven selection find topics
3. (Optional) Copy templates for advanced runs:
   - `config/run-policy.md.example` → `config/run-policy.md`
   - `config/signals.yaml.example` → `config/signals.yaml`
4. Test: "Run bottom feeder" (routine mode, 1 topic, Brave-only)
5. Review output. Calibrate.
6. Scale: "Run bottom feeder on [topic1, topic2, ...]" or fleet mode with a topic file

---

## Key docs

- `references/execution/execution-modes.md` — single / batched / supervised
- `references/execution/provider-fallback.md` — fallback chains
- `references/execution/checkpoint-monitoring.md` — long-run checkpoints
- `references/execution/recovery-patterns.md` — failure & drift recovery
- `references/topic-selection/context-driven.md` — primary topic selection
- `references/topic-selection/external-signals.md` — live operational signals
- `references/output/run-progress.md` — audit-trail format
- `references/output/strategic-synthesis.md` — cross-topic action plans
- `references/quality-gate/completion-checklist.md` — per-topic quality gate

---

## Scripts

- `scripts/provider-usage.sh` — provider usage snapshot (Tide Pools → legacy lobster → `openclaw status` fallback)
- `scripts/check-balance.sh` — parse budget from JSON (supports `remaining`, `balance`, `credits`, or `venice.data.diem`)
- `scripts/estimate-cost.sh` — rough relative cost estimate by mode/source count
- `scripts/check-provider-health.sh` — provider reachability preflight

All budget scripts are best-effort and never fail a run.

---

## Budget

Budget tracking is **informational only** — it never blocks runs.

- Scripts probe available balance best-effort
- If probes fail (missing tools, wrong provider), runs continue normally
- `min_reserve_usd` is a soft stop suggestion, not a hard gate
- Venice/Diem legacy fields preserved for backward compatibility
- **Multi-profile support**: if your provider has multiple auth profiles (team seats, API keys), the agent tracks rotation and flags when a profile is exhausted

---

## 🔧 Customization

### Topic seeds (`config/topics.md`)
Replace the default topics with what matters to your team. Organize by priority tiers — the agent picks the highest-value topics first. The more specific your seeds, the better the output. Context-driven selection (mining your PM tools, conversations, and team profiles) usually beats any curated list.

### Sources
Default: Brave search + local knowledge. Optional: Perplexity (deep synthesis), Twitter (sentiment), CoinGecko/CoinMarketCap (crypto data), browser (page extraction). See `references/research-sources.md` for the full source strategy.

### Execution & reliability
- Start with `execution_mode: single` in routine mode
- Use `execution_mode: batched`, `batch_size: 2-3` in burn mode
- Enable supervised mode + checkpoints for runs >2h
- Configure a `provider_fallback` chain instead of strict provider lock
- Keep subagents short-lived (1 topic each)

---

## Lessons from production

- Context-driven selection produces far better topics than generic seed lists
- Department playbooks have highest value per file (name real people, real tasks)
- Quality degrades after ~20 topics in one session — use checkpoints
- Cron safety nets save continuity for long burns
- Strategic synthesis should come last (ingredients before the meal)
- 20 deep files > 40 thin ones

---

Keep it useful, keep it auditable, keep it alive under failure.

**Ran rah. Click clack.** 🦞
