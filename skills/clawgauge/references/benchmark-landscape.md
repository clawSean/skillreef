# Benchmark Landscape

Checked against current upstream sources on 2026-08-16. Re-check primary
sources before a consequential campaign because these projects move quickly.

## Core local stack

### ShellBench

- Canonical repo: `openclaw/shellbench`
- Historical/public package and CLI name: ClawBench
- Best role: full agent + OpenClaw route comparison
- Current strengths: deterministic completion, trajectory and behavior scoring,
  repeated runs, pass^k, worst-of-n, bootstrap confidence intervals, failure
  modes, latency/tokens/cost, variance/SNR analysis, config/tool ablations, and
  native-eval traces across OpenClaw and other harnesses
- Current research runbook adds r0 route qualification, exact model/reasoning
  proof, pinned judge route, n=3 qualification, n=6 campaigns, trace retention,
  and explicit exclusion of infra-dominated or mixed-identity runs

This is the primary scored capability layer.

### OpenClaw Personal Agent QA

- Source: OpenClaw `qa run --qa-profile personal-agent`; `qa suite
  --preflight` is only the lower-level harness check
- Best role: regression, privacy, approval, tool-safety, and workflow gate
- Not a generic model benchmark and not a source of a quality score
- Must run with isolated home/state/config/XDG roots and synthetic fixtures

### OpenClaw character eval

- Source: OpenClaw `qa character-eval`
- Best role: persona naturalness, vibe, and humor for the fixed Gollum/C-3PO
  scenarios
- Preserves candidate transcripts and run stats; supports per-model thinking and
  fast mode, multiple judges, blind candidate labels, and judge concurrency
- Not a general intent benchmark; use at least two independently verified
  provider families and report disagreement

## Useful external patterns

- SWE-bench Verified: isolated repo execution and deterministic test outcomes
- tau-bench/tau2/tau3: simulated users, policy/tool APIs, repeated reliability
- WebArena/VisualWebArena: reproducible web environments and end-to-end success
- OSWorld: desktop/computer-use execution environments
- AgentBench: warns against overfitting to one agent domain
- GAIA/HAL: verified assistant tasks with cost/reliability disclosure
- eval-integrity: contamination, holdout, judge validity, statistical honesty,
  reproducibility, and exclusions

Borrow the methods; do not mix their public scores with local OpenClaw results.

## Optional future lanes

- `HKUDS/ClawWork`: 220 GDPVal-style economic tasks plus cost/quality/survival;
  useful for economic-value questions, not the default local route test
- `rdi-berkeley/agents-last-exam`: long-horizon, economically useful agent
  tasks with sandbox/artifact discipline; heavier infrastructure
- `steipete/aibench`: useful for OpenAI-compatible API behavior/performance,
  not an OpenClaw agent-quality replacement
- `steipete/tokentally`: useful semantics for normalized cached/reasoning
  tokens, exact price lookup, and preserving unavailable cost as null
- lm-evaluation-harness, OpenAI Evals, DeepEval, and LLMEvaluation: useful for
  output/model evaluation, but they do not reproduce the local OpenClaw tool and
  memory surface

## Third-party skill audit notes

ClawHub discovery on 2026-08-16 found several superficially relevant skills:

- `benchmark-model-provider`: useful ideas around user-specific prompt suites,
  versioned specs, raw artifacts, reranking, and pricing-source policy; local
  scan raised a critical suspicious finding, so it was not installed
- `model-benchmark`: generic Markdown guidance, no stronger harness
- `pinchbench`: failed security review; task checks execute arbitrary code and
  upload data, so it was rejected
- `eval-integrity`: clean and useful as an integrity checklist

ClawGauge borrows only reviewed concepts. It does not require these skills.

## Anti-patterns

- one universal score for unrelated work lanes
- one run per model
- judge-only rankings
- changing task sets or concurrency between models
- allowing fallback and crediting the primary
- treating missing metrics as zero
- comparing scores across OpenClaw/platform drift
- tuning prompts/tasks after seeing candidate results
- using private user data because it feels "representative"
