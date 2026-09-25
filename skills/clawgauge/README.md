# ClawGauge

[![OpenClaw](https://img.shields.io/badge/OpenClaw-skill-EA4AAA)](https://openclaw.ai)
[![ShellBench](https://img.shields.io/badge/ShellBench-compatible-2563EB)](https://github.com/openclaw/shellbench)
[![Python](https://img.shields.io/badge/Python-3.9%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)

Gauge models as working agents, not just leaderboard entries.

This OpenClaw skill combines:

- **ShellBench** for deterministic capability, trajectory quality, repeated
  reliability, failure modes, latency, tokens, and cost.
- **OpenClaw Personal Agent QA** as a fail-closed ten-scenario safety and
  regression gate.
- **Blind character evaluation** for persona/naturalness evidence, kept
  separate from deterministic capability and general intent claims.
- **Versioned evidence envelopes** that prove the exact requested and observed
  route, reasoning/fast state, fallback state, commits, task fingerprint,
  judge identity, campaign protocol, content-bound cache telemetry, and
  optional pricing provenance.
- **Deterministic truthfulness gates** for false premises, failed-tool claims,
  unsupported citations, abstention, and over-refusal.

## What it answers

- Can this model operate reliably as an OpenClaw-style agent?
- Which model performs better on the same tasks and tool surface?
- Does a cheaper model still win after explicit quality, reliability, and
  worst-of-n floors are enforced?
- What failure modes appear across repeated runs?
- Which route should handle daily operation, coding, research/browser work,
  background tasks, persona, or escalation?

It does **not** claim that a single score measures general intelligence or user
intent understanding. For those questions, use representative tasks and an
explicit rubric.

## Install

Copy this repository into your OpenClaw workspace skills directory:

```bash
git clone https://github.com/clawSean/clawgauge \
  ~/.openclaw/workspace/skills/clawgauge
```

Then start a new OpenClaw session so the skill catalog refreshes.

## Start here

Read [`SKILL.md`](SKILL.md) for the workflow and safety constraints.

For a small two-route coding screen, use the v5 personal campaign described in
[`personal-campaign-safety.md`](references/personal-campaign-safety.md). It fixes
implicit Gateway targeting and whole-answer memo reuse, bounds 18 serial cells,
and distinguishes requested controls from independently observed identity.
Provider-free lifecycle/native-schema checks do not establish real-provider
readiness; subscription handoff and native route qualification remain separate
prerequisites. No hard dollar cap, OS sandbox, or benchmark winner is claimed.

The main helpers are:

- `scripts/run_personal_campaign.py` — freeze and supervise the bounded screen.
- `scripts/personal_campaign_worker.py` — disposable cell lifecycle and explicit endpoint.
- `scripts/personal_campaign_config.py` — reject unsafe prepared-config overrides.
- `scripts/analyze_personal_campaign.py` — summarize native scores and evidence gaps.

- `scripts/inspect_checkouts.py` — record Mac/checkouts, commits, dirty state,
  and upstream drift without fetching.
- `scripts/run_personal_agent_preflight_isolated.sh` — provider-free isolated
  QA harness proof.
- `scripts/run_openclaw_qa_gate.py` — full-profile, exact-route QA campaigns.
- `scripts/score_qa_suite.py` — fail-closed attempt and terminal-result scoring.
- `scripts/qualify_prefix_cache.py` — zero-call plan or fail-closed
  cold/warm/exact-replay qualification of an already-running loopback MLX
  service; grants direct-service reuse only and rejects response-memo false
  greens.
- `scripts/build_local_cache_admission_plan.py` — freeze exact provider,
  response/loaded model, installed OpenClaw build, and architecture-specific
  local-cache identity; plan generation alone proves nothing.
- `scripts/validate_local_cache_admission.py` — content-bind every planned case,
  exact OpenClaw route/fallback observation, architecture manifest, and runtime
  epoch before granting `cache-qualified`.
- `scripts/build_evidence_envelope.py` — wrap untouched ShellBench results with
  ClawGauge-owned provenance.
- `scripts/build_cache_trace.py` — bind per-request cache/lifecycle telemetry to
  one immutable artifact.
- `scripts/compare_clawbench_results.py` — protocol-aware quality/value
  comparison with fail-closed Core-19, QA, truthfulness, and local-admission
  requirements for decision-grade status.
- `scripts/estimate_campaign.py` — cache-profile-matched expected/p90 wall-time
  estimate before an expensive run.
- `scripts/build_truthfulness_plan.py` — frozen, content-bound n>=3 execution
  cells for the deterministic truthfulness suite.
- `scripts/score_truthfulness.py` — n>=3 content-bound deterministic
  truthfulness gate; judges stay advisory.
- `scripts/summarize_character_eval.py` — attested blind persona evidence.
- `scripts/self_test.py` — provider-free regression and adversarial checks,
  including the loopback cache qualifier and truthfulness scorer.
- `scripts/test_decision_grade.py` — adversarial stale/tampered QA, local
  admission, and coverage-gate tests.

The included fixtures are synthetic, and the QA helpers isolate state and
allowlist environment variables. Do not feed private chats, real credentials,
or personal memory into benchmark runs.

## Repository model

The live source is maintained in the contributor's OpenClaw workspace. This repository and
the SkillReef copy are generated from the same scrubbed build so the public
surfaces stay synchronized.
