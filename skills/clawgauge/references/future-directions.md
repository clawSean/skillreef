# Future Directions

Only promote these after the core QA + character + ShellBench workflow has
produced credible local comparisons.

## 1. Sanitized system-fit cards

Create 8–12 versioned, fake-data tasks matching the work lanes that matter:

- ambiguous request and intent inference
- additional code/repo changes with verification beyond the required pinned
  coding task used for coding-lane decisions
- cited research memo
- privacy-safe memory recall
- tool failure recovery
- approval/denial followthrough
- concise Telegram-style response
- reviewer catching an attractive but wrong result

Keep hidden expected outcomes and deterministic checks. Freeze the cards before
running candidates; maintain a holdout set to resist prompt/task overfitting.
This supplements ShellBench—it does not replace it or become a vanity
"SeanBench" leaderboard.

## 2. Longitudinal routing registry

Store comparable run manifests and lane decisions so model aliases, provider
changes, OpenClaw upgrades, and price changes can invalidate stale guidance
explicitly. Never compare raw scores across platform drift.

## 3. Operational telemetry

Track real-world usage separately from evaluation:

- longitudinal provider/model/runtime tokens and cache-counter trends
- fallback/retry rate
- quota windows
- latency and spend
- sanitized failure taxonomy

This answers "what are we spending and where is it failing?" rather than "which
model is capable?" Decision-grade cache identity and per-campaign hit evidence
are already required by the core envelope; this section is ongoing monitoring.

## 4. External harness adapters

- ClawWork for economic-value tasks
- Agents' Last Exam for long-horizon sandboxed work
- browser/desktop suites when computer use becomes a routing decision
- cross-harness OpenClaw vs Codex/Claude Code/Hermes comparisons

Use remote disposable compute and the upstream campaign runbook for this work.

## 5. Statistical extensions

- paired task-level bootstrap deltas
- model-order and time-window effects
- sequential stopping calculations
- judge calibration and cross-provider agreement
- task SNR retirement/replacement policy
- explicit non-inferiority margins by work lane
