# ClawGauge Evaluation Method

This is the normative method for comparing exact OpenClaw model routes. The
goal is a reproducible routing decision, not a decorative leaderboard.

## 1. Define the decision

Write the decision before seeing results:

- baseline and candidate exact provider/model routes
- required work lanes
- unacceptable failures
- maximum spend and wall time
- minimum acceptable quality/reliability
- whether the result is local guidance or a publishable claim

Do not change the success rule after seeing which model wins. If the decision
changes, start a new run ID.

## 2. Freeze the protocol

The manifest must pin:

- OpenClaw version and git commit
- ShellBench version, git commit, release IDs, and task fingerprint
- model/provider request and observed identity
- reasoning/thinking and fast/priority state
- adapter/harness, tool/profile fingerprint, and cache runtime/config fingerprint
- fallback/retry policy and normalized cache reset/reuse profile
- judge model, reasoning, and whether judges affect score
- task IDs, variants, repetitions, concurrency, and model order
- pricing source/date and currency

The comparator treats missing core fields or drift in these axes as a blocker.
Different models/providers are expected; different evaluation protocols are not.

## 3. Control temporal and order effects

Provider behavior and load change over time.

- Run baseline and candidate in the same time window.
- Interleave by task/repetition when practical: A1, B1, B2, A2, then reverse.
- Keep concurrency fixed and low enough to avoid rate-limit artifacts.
- Preserve retries and exclusions; do not silently replace a bad run.
- Label quota, auth, transport, and host failures as infrastructure.

## 4. Evidence and provenance

| Layer | What it proves | Default |
|---|---|---|
| Mock QA preflight | Harness works in an isolated envelope | 1 run |
| ShellBench r0 | Exact route, model, reasoning, tools, traces, usage | 1 non-scoring qualification per route |
| Personal Agent QA | Selected regression/safety scenarios pass | Every candidate and baseline |
| Character eval | Persona/naturalness preference | Blind, >=2 verified provider-family judges |
| Cache-aware quick screen | Reject unusable routes before a full campaign | cold/warm tool loop + 3 tasks, n=1 |
| Local cache admission | Architecture, isolation, memory, and lifecycle correctness | Every enabled local MLX route |
| ShellBench Standard Mac | Directional capability and reliability | 9 pinned tasks, n=3 |
| Core-19 | Broad local OpenClaw capability | When close or consequential |
| Research campaign | Reproducible external claim | Upstream runbook, n=6 |

No lower layer substitutes for a higher one. In particular, mock QA is not a
real-model test, character judging cannot rescue a task failure, and a public
leaderboard number is not a local OpenClaw result.

Native ShellBench artifacts and ClawGauge decision evidence are different
schemas. Preserve the native result unchanged, then build a versioned
ClawGauge evidence envelope that links it to independently collected route,
judge, host, campaign, retry, and pricing attestations. Never claim those
attestations came from a native result field when they did not.

## 5. Task selection

After r0, run a cache-aware quick screen: one cold streamed request followed by
a realistic append-only tool continuation, then coding/repo, research/tool, and
truthfulness tasks at n=1. Reject routes that miss identity, correctness,
warm-hit, memory, or interactive/background latency floors. Estimate the full
campaign from that matching cache-profile pilot with `estimate_campaign.py`.

Survivors run the pinned Standard Mac nine-task set in
`shellbench-core-v1.md` at n=3. Controlled cache trials
start each task repetition fresh, reuse one server within the task, and prevent
cross-task reuse. Route-native and controlled trials use separate run IDs and
their latency is never pooled.

Add `t4-memory-recall-continuation` for memory-heavy routing decisions.

`t5-hallucination-resistant-evidence` is a separate trust canary. The
2026-08-16 ShellBench manifest reports cross-model SNR around 0.25, so it should
not influence rank until a newer signal study says otherwise.

Run the deterministic eight-case truthfulness suite in
`truthfulness-suite-v1.json` at n>=3. Seven cases cover nonexistent-file bait,
failed-tool completion claims, unsupported citations, false-memory premises,
conflicting evidence, and correct abstention; the eighth controls for
over-refusal. Its content-bound deterministic gates decide pass/fail; judge
scores are advisory. The immutable plan, results, attempt evidence, and every
cell execution trace bind the exact requested/observed
provider/model/adapter/reasoning/fast route and fallback=false. A copied frozen
response or fixture event list without that independent trace cannot earn route
attribution. Bind passing scores into each envelope; missing or mismatched
scores leave trust and decision-grade comparison unavailable.

For a coding-specific decision, require `t1-bugfix-discount`,
`t2-add-tests-normalizer`, and at least one pinned repo task rather than
overweighting generic file work. For intent/autonomy, add
dedicated frozen ambiguous-intent scenarios; the current fixed character pack
does not measure general intent inference.

## 6. Repetition and uncertainty

- n=1: `routing-smoke`; never decisive
- n=2: repeated routing evidence, still below directional confidence
- n>=3: eligible for `directional` evidence
- Core-19, clean route proof, n>=3, confidence intervals, and all gates:
  eligible for `decision-grade` local guidance
- n=6 with upstream campaign controls: research-grade input

Always report bootstrap confidence intervals when ShellBench emits them.
Non-overlapping intervals are stronger evidence than a raw score delta.
Overlapping intervals mean "no clear aggregate leader," not "tie." Inspect
task-level and reliability differences before deciding whether another run
would change the action.

Use sequential stopping:

1. run r0
2. run n=3 smoke
3. stop if a route is invalid or the decision is already obvious and low-risk
4. expand only close, high-impact, or contradictory results to Core-19/n=6

The comparator enforces this fail closed. `decision-grade` requires unblocked
Core-19 at n>=3, comparable route-bound truthfulness, comparable content-bound
full Personal Agent QA, and passing current local-cache admission for every
enabled local MLX route. Standard Mac remains directional. A one-task n=3 run
is not decision-grade.

## 7. Route identity

A route is clean only when:

- requested provider/model equals the observed model on every trace
- requested reasoning is present in request/proxy evidence when supported
- fallback is explicitly off
- auth and quota errors are absent
- judge identity is independently proven
- tool calls, traces, token usage, and artifacts are complete

An alias alone is not identity proof. A response that "looks like" a model is
not identity proof.

## 8. QA gate

A live candidate passes only when the complete pinned ten-scenario
`personal-agent` profile in `personal-agent-profile.md` (or an explicitly
declared narrowed profile) passes with:

- primary and alternate model equal
- one provider mode and one requested/effective fast configuration
- no stalls, blocks, or skips
- complete summary/evidence artifacts
- every expected model/scenario cell present in the run manifest
- every retry and failed attempt retained

QA scenario sets must match across compared models. `preflight` is bootstrap
evidence only. A mock provider yields `harness-only` only after every expected
harness check passes; a failed mock run is still a failure.

Bind the final QA scorecard by relative path and SHA-256 in each evidence
envelope. Missing QA keeps capability evidence directional; a supplied stale,
tampered, mismatched, or failed-retry scorecard blocks validation.

Fast mode is tri-state: requested `unset`, `true`, or `false`, plus the
effective value observed in each summary. Omission must never be recorded as
explicit false. If the current CLI cannot pin false, report that route as
blocked instead of fabricating an off setting.

## 9. Persona and naturalness evidence

The current upstream fixed scenarios are Gollum and C-3PO. They measure persona
naturalness/funniness plus a small file task; they are not a general intent
benchmark. Pin:

- the same scenario/persona for every candidate
- candidate reasoning/fast setting
- at least two judges from independently verified provider families
- blind candidate labels
- complete transcripts or cryptographic transcript hashes and run status
- requested and observed judge identity, reasoning proof, and scenario
  fingerprint

Report mean rank, mean score, wins, rank dispersion, top-choice agreement, judge
failures, and qualitative strengths/weaknesses. Ranks must be integral,
non-boolean, unique, and cover every candidate. Treat split judges as
uncertainty, not a problem to average away. Candidate run failure or missing
transcript evidence blocks the comparison.

## 10. Cache, cost, and speed

Never infer price from model family. Record exact:

- cache kind/runtime/version/engine/capacity and canonical config fingerprint
- per-request content-hashed cache events joined to task/repetition/turn IDs
- PID/start/runtime/cache epoch, gross/cached/uncached/written tokens, and post-warm misses
- startup/readiness, cold/warm request, TTFT/prefill/decode, tool, and end-to-end task timing kept separate
- input, cached-input, output, and reasoning token rates
- pricing source and date
- currency and measured spend when available

Operational routing uses end-to-end task wall time; request timing diagnoses
cache behavior and never substitutes for task latency. Route-native and
controlled traces are never pooled. Cache profile/reset/reuse drift blocks;
route engines/capacities may differ.
Full-response memo hits block repeated quality/trust trials; missing cache-hit evidence makes speed `n/a`.
Missing pricing evidence makes cost `n/a`; zero is valid only when explicitly free.

For local routes, direct-service prefix reuse and route-level cache admission
are separate claims. `qualify_prefix_cache.py` proves only direct-service
cold/warm/replay reuse. `build_local_cache_admission_plan.py` plus
`validate_local_cache_admission.py` enforce architecture, isolation, memory,
lifecycle, exact OpenClaw route, and fallback evidence. Cache admission never
substitutes for ShellBench, truthfulness, or QA operator qualification.

Value means the cheapest route that clears explicit quality, reliability, and
worst-of-n floors (and pass^k when required)—not simply the lowest cost/pass in
the table. A value comparison without declared floors is unavailable.

## 11. Decision synthesis

Do not invent a universal weighted score. For each requested lane:

1. require clean route identity
2. require the relevant QA gate
3. establish deterministic capability/reliability floor
4. use character evidence where human interaction matters
5. compare latency/cost only among routes that cleared the floor

Use only:

- `adopt`
- `adopt-for-<lane>`
- `keep-baseline`
- `indeterminate`
- `blocked`

`adopt` requires no hidden critical regression. If the candidate is excellent
for cheap background work but weaker at ambiguous judgment, say
`adopt-for-background`, not `adopt`.

## 12. Integrity checklist

- [ ] Decision and success rule written before results
- [ ] Synthetic/public data only
- [ ] Commits/releases/task fingerprints pinned
- [ ] Exact observed route and downstream router/mixed identity/cache/fallback proven
- [ ] Same task set, runs, adapter/tools, judge policy, and time window
- [ ] Fallback off and failures preserved
- [ ] n and confidence intervals reported
- [ ] QA and character evidence kept separate from scored capability
- [ ] Pricing source recorded or cost marked unavailable
- [ ] Exclusions and infra failures listed
- [ ] Raw traces and artifacts retained
