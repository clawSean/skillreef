---
name: "clawgauge"
description: "Compare OpenClaw routes with cache-safe, attributable quality and performance evidence."
---

# ClawGauge

ClawGauge answers: **which exact model route is best for which work lane in
this OpenClaw system, with what confidence and tradeoffs?** It does not invent a
universal leaderboard winner.

Read `references/evaluation-method.md` before a consequential run. Load only the
other references named by the relevant workflow step.

## Evidence stack

- **ShellBench**: deterministic capability, trajectory, behavior, repeated
  reliability, failure modes, latency, tokens, and cost.
- **Personal Agent QA**: ten-scenario synthetic regression/safety gate. A pass
  is not a quality score; preflight is harness evidence only.
- **Character eval**: blind persona/naturalness evidence for the fixed
  Gollum/C-3PO scenarios. It is not general intent evidence.
- **ClawGauge evidence envelopes**: explicit route, cache, judge, campaign,
  release, and optional pricing attestations around untouched native results.

## Hard rules

1. Compare exact routes: provider, model ID, adapter, reasoning, requested and
   effective fast/priority state, fallback, tools/profile, OpenClaw commit,
   ShellBench commit/release/task fingerprint, cache treatment, judge route,
   and run protocol.
2. Require strict identity. Alias/fallback blocks; router or mixed routes need
   complete downstream identity/cache/fallback proof. Full-response memo hits block repeated quality/trust trials.
3. Use only synthetic or intentionally public fixtures. Never use live chats,
   private memory, real secrets, or production delivery.
4. Never mutate an upstream source tree to make a catalog or verifier pass.
5. Never install/upgrade dependencies, alter live OpenClaw routing/config, or
   restart Gateway as part of a benchmark without explicit approval.
6. Missing evidence stays `n/a`. Preserve raw artifacts, failed attempts,
   retries, exclusions, and infrastructure classifications.
7. Mock providers prove harness health only. One real run proves routing only.
8. An LLM judge never rescues a deterministic failure.

## Decision lanes

- daily operator: completion, judgment, reliability, and cost
- coding/file work: deterministic coding/repo completion and verification
- research/browser: citation, evidence, browser, and tool-use discipline
- conversation/persona: naturalness without deterministic or QA regression
- background/cheap: cheapest route clearing explicit capability floors
- reviewer/escalation: ambiguity handling, verification, and error detection

Different routes may legitimately win different lanes.

## Workflow

### 1. Freeze the decision

Before results, record baseline/candidate exact routes, target lanes,
unacceptable failures, minimum quality/reliability/worst-of-n floors, optional
pass^k requirement, cache profile, maximum spend, and stopping rule.

If live spend may be material and no budget was given, finish the plan and ask
once before provider calls. Read-only discovery and provider-free checks may
continue.

### 2. Inventory local checkouts

```bash
python3 skills/clawgauge/scripts/inspect_checkouts.py \
  --out <run-dir>/checkout-audit.json
```

This records the local Mac host, commits, dirty state, and known tracking-branch
drift without fetching. A stale/dirty checkout is a warning or blocker; it is
never silently called current.

For publication-grade ShellBench work, load the native upstream campaign
runbook from the pinned commit. Publication uses its combined suite and remote
beasts, not a hard-coded local Core-19 campaign.

### 3. Prove QA harness health

```bash
bash skills/clawgauge/scripts/run_personal_agent_preflight_isolated.sh
```

This uses `env -i`, disposable HOME/OpenClaw/XDG roots, and a mock provider.
It proves only that the QA harness boots.

Resolve a no-call plan for the full profile:

```bash
python3 skills/clawgauge/scripts/run_openclaw_qa_gate.py \
  --model <baseline-provider/model> \
  --model <candidate-provider/model> \
  --repetitions 1 --plan
```

The default is the complete profile in
`references/personal-agent-profile.md`. Repeated `--scenario` explicitly
narrows it. `--fast` requests on; omission records `unset` and the scorer
compares the effective value from artifacts. The current CLI cannot reliably
pin off, so an explicit-off requirement blocks until the upstream route can
prove it.

Live auth must be opt-in by variable name, for example
`--pass-env PROVIDER_API_KEY`; unrelated ambient variables and real HOME are
not inherited. Remove `--plan` only after auth/spend approval, then score:

```bash
python3 skills/clawgauge/scripts/score_qa_suite.py \
  --run-dir <qa-run-dir> \
  --out <qa-run-dir>/qa-gate.md \
  --json <qa-run-dir>/qa-gate.json
```

A live route passes only when every expected scenario passes on every retained
attempt, fallback is disabled, profile evidence is complete, and no run stalls,
blocks, skips, or goes missing. Nonzero scorer exit means do not adopt.

### 4. Run ShellBench capability trials

Qualify every route with upstream r0 first. Prove requested/observed model,
reasoning/fast state, tools/traces/usage, independent judge identity, and zero
fallback/auth/quota substitution.

On ClawPop, default to the pinned Standard Mac nine-task subset at n=3 in
`references/shellbench-core-v1.md`. It includes deterministic coding, repo,
browser, privacy, research, and delegation work. Coding claims require
`t1-bugfix-discount`, `t2-add-tests-normalizer`, and a repo task such as
`t2-config-loader`. Expand close or consequential decisions to exact Core-19.
Report `t5-hallucination-resistant-evidence` separately as a low-SNR trust
canary.

Pin one normalized cache profile for both routes and classify cache kind. For
controlled cold-then-warm, reset each repetition, reuse within-task only, and
never pool route-native latency or full-response memoized quality/trust trials.

Preserve each native ShellBench result unchanged. Build a ClawGauge envelope
from an independently assembled attestation:

```bash
python3 skills/clawgauge/scripts/build_evidence_envelope.py \
  <native-result.json> --attestation <attestation.json> \
  --out <route-evidence.json>
python3 skills/clawgauge/scripts/summarize_clawbench_result.py \
  <route-evidence.json>
```

Compare equivalent envelopes:

```bash
python3 skills/clawgauge/scripts/compare_clawbench_results.py \
  --baseline <baseline-evidence.json> \
  --candidate <candidate-evidence.json> \
  --objective quality --json <comparison.json> --out <comparison.md>
```

For value, declare all floors:

```bash
python3 skills/clawgauge/scripts/compare_clawbench_results.py \
  --baseline <baseline-evidence.json> \
  --candidate <candidate-evidence.json> --objective value \
  --min-score 0.70 --min-reliability 0.80 --min-worst-of-n 0.55
```

Add `--require-pass-hat-k` when the lane demands it. Missing price provenance
makes cost/value unavailable but does not erase valid capability evidence.
See `references/evidence-envelope.md`.

### 5. Measure persona/naturalness

Use current `pnpm openclaw qa character-eval --help`; pin candidates and at
least two judges from independently verified provider families, keep judges
separate from candidates, and blind labels. Then attach the evidence contract:

```bash
python3 skills/clawgauge/scripts/summarize_character_eval.py \
  <character-eval-summary.json> \
  --attestation <character-evidence.json> \
  --out <character-summary.md> --json <character-summary.json>
```

Missing transcript hashes, scenario fingerprint, observed judge identity,
reasoning proof, or blind-label proof blocks/provisionalizes this layer. See
`references/character-evidence.md`.

### 6. Synthesize by lane

Prioritize: route validity; deterministic completion and safety; repeated
reliability/worst-of-n; trajectory and verification; task deltas; persona
evidence; latency/cost; advisory judge scores.

Use confidence `routing-smoke`, `insufficient-repeats`, `directional`, or
`decision-grade`. Directional requires comparable n>=3 evidence.
Decision-grade local guidance additionally needs fit-for-purpose/Core-19
coverage, clean QA, proven identity/reasoning, retained artifacts, and reported
uncertainty.

Use one verdict: `adopt`, `adopt-for-<lane>`, `keep-baseline`,
`indeterminate`, or `blocked`. ShellBench alone never earns full-system
decision-grade.

## Report and validation

Start with verdict, confidence, and strongest limitation. Then provide the lane
matrix, comparable task deltas, QA status, persona disagreement, cost source,
cache evidence, failures/exclusions, artifacts, and next action. Use
`templates/model-quality-report.md`.

Provider-free regression check:

```bash
python3 skills/clawgauge/scripts/self_test.py
```

Keep run artifacts under `skills/clawgauge/runs/<run-id>/`; publish only
deliberately scrubbed evidence. Historical VPS paths are not current runtime.
