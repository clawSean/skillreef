# Upstream and Mac Audit — 2026-08-16

## Local state observed

- OpenClaw installed version: `2026.7.1`
- Local source checkout: `$HOME/projects/openclaw`
- Checkout commit during audit: `20be26c...`
- A later same-day read-only check found upstream at
  `8277cb24a16ca783c841a3af9bc761fc4103600b`; the local checkout was then 867
  commits behind and had an
  unrelated untracked project directory. Nothing was pulled or modified.
- macOS arm64 does not provide GNU `timeout` by default.

These facts are an audit snapshot, not a claim about the version at future run
time. Every benchmark must record its own actual commit/version.

## ShellBench observations

- GitHub redirects `openclaw/clawbench` to `openclaw/shellbench`.
- Audited checkout commit:
  `884dd1bb55112c93292e1633081d62504ba49905` (2026-07-29).
- The package/CLI still use the ClawBench name in places.
- Core v1 contains 19 signal-curated public tasks.
- Current result schema includes completion, trajectory, behavior, judge
  coverage, reliability, pass^k, worst-of-n, bootstrap CI, latency, token/cost,
  failure modes, task/release fingerprints, and environment metadata.
- The upstream research skill requires r0 route qualification, model/reasoning
  proof, pinned harness/judge/task commits, n=3 qualification, n=6 research
  runs, raw trace retention, and exclusion of mixed-identity or infra-dominated
  runs.
- `t5-hallucination-resistant-evidence` is explicitly low-SNR for cross-model
  ranking (about 0.25 in the audited manifest). It remains useful as a trust
  canary.

## OpenClaw QA observations

- Personal Agent QA is a ten-scenario binary safety/regression profile invoked
  with `qa run --qa-profile personal-agent`; preflight is harness evidence.
- The runtime taxonomy, not the prose scenario table, determines exact profile
  membership. At the audited commit it selects `agent-tool-safety-approvals`
  as the primary owner for `agent-runtime.tool-safety-controls`; the prose
  table's `personal-tool-safety-followthrough` entry is stale/secondary.
- Commit `22dd3d4ed0ba50d40d494ee23136a38fcbe27d5c` changed fast-mode handling
  to preserve unset versus explicit false in programmatic calls. ClawGauge must
  record requested and effective state separately.
- `qa character-eval` currently has two fixed persona scenarios (Gollum and
  C-3PO). It
  supports per-candidate thinking/fast settings, multiple judges, blind labels,
  concurrency controls, transcripts, durations, rankings, and JSON/Markdown
  artifacts, but it does not prove general intent inference.
- Source-defined model defaults change rapidly. ClawGauge now pins explicit
  routes for comparisons and refers to current source docs instead of freezing
  a moving default model list.
- `scripts/bench-model.ts` is a narrow hard-coded latency helper, not a general
  model benchmark.

## Defects corrected in ClawGauge

1. Replaced VPS-only `~/...` defaults with Mac-safe `$HOME/...` paths.
2. Replaced GNU `timeout` dependency with Python process-group timeouts.
3. Removed credential scraping from Codex auth JSON.
4. Removed scenario-catalog file quarantine/source mutation.
5. Renamed QA "score" language to a pass/fail gate.
6. Made missing comparison fields unavailable/blocking instead of zero.
7. Added strict protocol comparability and nonzero exit on mismatch.
8. Added CI, route identity, reasoning, fallback, and task-fingerprint checks.
9. Added character/intent summarization with blind multi-judge disagreement.
10. Separated the low-SNR t5 trust canary from ranking tasks.
11. Replaced universal winner language with task-specific route decisions.
12. Added confidence levels and the verdict vocabulary used by the operating
    workflow.
13. Added a versioned ClawGauge evidence envelope instead of treating custom
    attestations as native ShellBench fields.
14. Made the full Personal Agent profile the default live QA gate; preflight
    remains explicitly harness-only.
15. Added strict attempt preservation, expected-cell checks, fail-closed exit
    status, allowlisted subprocess environments, fast tri-state evidence, and
    value floors.

## Security/discovery notes

- ShellBench remained at
  `884dd1bb55112c93292e1633081d62504ba49905` during the same-day recheck.
- `steipete/aibench` had no new benchmark-method change; TokenTally's
  null-cost and token-normalization semantics were reviewed for adoption.
- No third-party benchmark skill was installed.
- `pinchbench` was rejected after a security failure.
- `benchmark-model-provider` was not installed after a suspicious scan.
- The incomplete temporary inspection environment created during discovery was
  moved to Trash; no dependency install remained.
