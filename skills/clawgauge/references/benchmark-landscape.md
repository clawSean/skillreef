# Benchmark Landscape Notes

Use these as orientation, not as a replacement for current primary-source checks.

## High-Signal Existing Approaches

- OpenClaw Personal Agent Benchmark Pack: local privacy-preserving personal assistant workflows through `qa-channel`; explicitly not a generic model benchmark. Best fit for OpenClaw personal-agent behavior.
- ClawBench (`openclaw/clawbench`): trace-scored full-stack agent benchmark. Best fit for model + harness + config quality.
- SWE-bench / SWE-bench Verified: real GitHub issue resolution, isolated code execution, deterministic test validation. Best fit for coding-agent proof.
- tau-bench / tau2/tau3-bench: simulated user conversations plus domain tools and policies; pass^k reveals consistency decay across repeated runs. Best fit for tool/API and policy-following agents.
- WebArena / VisualWebArena: self-hosted realistic web environments and end-to-end task success. Best fit for browser agents.
- OSWorld: real desktop/computer-use environment with setup and execution evaluators. Best fit for GUI/multimodal computer-use agents.
- AgentBench: multi-environment agent benchmark; useful warning against overfitting to one task family.
- GAIA / HAL: general assistant benchmark and leaderboard surfaces that emphasize tool use, cost, verified results, and confidence/reliability reporting.

## What To Borrow

- Isolate state per run.
- Prefer deterministic verifiers.
- Record harness and config details.
- Use repeated runs; expose pass^k and worst-of-n.
- Preserve tool-call traces.
- Report cost/tokens/latency.
- Classify failure modes.
- Treat harness failures separately from model failures.

## What Not To Do First

- Do not build a custom leaderboard before proving local benchmark execution.
- Do not use live private user data.
- Do not add a broad LLM judge before deterministic checks are stable.
- Do not compare public leaderboard numbers directly to local OpenClaw-agent runs; harness and tool surface matter.
