# Reference Resource Assessment

JPop's criticism was correct: the GPT 5.5 vs Grok run only produced binary QA pass/fail plus wall time. That is useful harness evidence, but it is not the useful score comparison the benchmark project was supposed to produce.

## What The Resources Actually Say

### Personal Agent Benchmark Pack

Local docs: resolve the active OpenClaw package root, then read
`docs/concepts/personal-agent-benchmark-pack.md`. On ClawPop the global
package tree is under the Mac user's npm prefix, not Linux `/usr/lib`.

The pack is explicitly a small local QA scenario pack for personal assistant workflows. The docs say it is not a generic model benchmark. It is best used as a privacy-safe OpenClaw agent behavior gate:

- fake users/preferences/secrets
- qa-channel, not live chats
- deterministic pass/fail scenarios
- personal-agent behavior checks such as reply routing, redaction, memory recall, approval denial, and proof-backed completion claims

Use it to answer: "Can this model survive our OpenClaw personal-agent safety/reliability smoke?"

Do not use it alone to answer: "Which model is better?"

### ShellBench

Source checked: canonical `openclaw/shellbench` README, Core v1 task docs,
`CLAWBENCH_V0_4_SPEC.md`, and schema/CLI code. Historical package/CLI surfaces
still use the ClawBench name.

ShellBench is the resource that actually matches useful model comparison:

- Core v1 has 19 signal-curated public tasks.
- Official policy is 3 runs per task.
- Results include `overall_score`, `overall_completion`, `overall_trajectory`, `overall_behavior`, `overall_reliability`, `overall_pass_hat_k`, `overall_worst_of_n`, latency, token, cost, per-task scores, and failure modes.
- Scoring is trace-based: completion 40%, trajectory 30%, behavior 20%, judge advisory by default.
- LLM judge output must not rescue failed deterministic checks.
- Exact score comparisons require same ClawBench commit, OpenClaw version, task set, run count, profile/tool surface, and provider routing.

Use it to answer: "Which model/config is better, how reliable is it, what failed, and what did it cost?"

## Skill Correction

The skill should treat Personal Agent Pack as a prerequisite safety/regression
gate and ShellBench as the primary scored comparison path. Native ShellBench
results remain untouched; ClawGauge adds a separate evidence envelope for
route, campaign, judge, and pricing proof. QA pass-rate reports should be named
"QA gate results" or "smoke pass-rate", not "model quality score."
