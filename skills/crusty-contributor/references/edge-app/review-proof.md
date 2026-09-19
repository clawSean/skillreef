# EdgeApp Review and Proof Playbook

Use for any non-trivial EdgeApp implementation, review, or pull request. This
playbook captures repeated patterns from merged work; target-repo instructions
and current source remain authoritative. The Edge proof contract owns the
required state and reviewer packet; this playbook owns evidence quality.

## Reconnaissance before editing

1. Find two to five comparable merged PRs in the target repository and, for a
   cross-repo change, in both owner and consumer repositories.
2. Read the final diff and final code, not only the PR title or generated
   summary. Read human review threads where the implementation changed.
3. Inspect neighboring tests, fixtures, PR-template proof, and current repo
   review rules. Copy the established proof shape when it tests the same kind
   of contract.
4. Record the exact target branch, dependency versions, feature/config gates,
   and whether local or test-only behavior differs from production.
5. Separate the requested job from adjacent cleanup. Do not enlarge an external
   contribution merely because nearby code is imperfect.

## Make every test discriminate

A passing test is useful only when it would catch the regression.

- State the invariant in the test name or assertion message.
- Reproduce the old failure with the previous code, a focused mutation, a
  golden vector, or a reference artifact when practical.
- Pair full-output fixtures with smaller property tests. Examples include exact
  CSV output plus column-mapping assertions, exact signature bytes plus
  independent verification, or a live-response fixture plus perspective tests.
- Assert the meaningful event, not a proxy. For provider probes, count calls by
  endpoint and distinguish quote from order creation; total request count can
  pass for the wrong reason.
- For async work, assert sequencing, stale-attempt suppression, cancellation,
  cleanup, retries, and partial-start failure where applicable.
- For compatibility work, test the old default and the new opt-in path.
- Inspect why the test passes after rebases or broad rewrites. Stray setup can
  make the assertion green without exercising the intended path.
- If a regression test cannot be shown to fail against old behavior, explain
  why its discriminating power is still trustworthy.

## Label evidence honestly

For each claimed proof, record:

- exact revision or head SHA;
- command, test count, platform, device, and relevant configuration;
- real, fake, stubbed, forced, or synthetic inputs;
- whether the path was actually executed or only compiled;
- what the evidence proves and what remains unproven.

A forced screenshot proves rendering, not organic reachability. A Maestro YAML
edit proves syntax, not device execution. A simulator pass proves that
environment, not both native platforms. Local config used to reveal a provider
or state belongs in the proof record and must be reverted or kept out of Git.

Avoid theatrical QA. If an unregistered template and docs cannot enter the
runtime bundle, prove the built bundle is unchanged instead of pretending an app
drive exercised the edit.

## Human and automated review freshness

Automated review is advisory evidence.

- Tie bot findings and human approvals to the reviewed SHA or changed blobs.
- After a rebase, autosquash, dependency bump, or large review round, compare the
  final diff and re-check unresolved human threads.
- Treat generated summaries as potentially stale. Verify every behavior claim
  against final code, especially limitations and persisted state.
- A green bot does not override a human request for changes, an unresolved
  product question, or contradictory runtime evidence.
- If identical blobs receive inconsistent automated verdicts, trust direct code
  and test analysis and record the inconsistency.
- Before merge or handoff, confirm current review state, current head, CI, and
  the absence of superseded claims in the PR body.

## Responding to review

For each material thread, use one of these explicit dispositions:

- Valid: fix it, name the commit/fixup, and give focused proof.
- Partly valid: fix the reachable portion and explain the boundary.
- Not introduced here: identify whether it is pre-existing or newly reachable,
  then record the rollout gate or follow-up if it matters.
- Contract or product decision: present scenarios and tradeoffs, then wait for
  the owner rather than disguising a preference as a defect.
- Declined: trace the relevant semantics and explain why the suggested
  abstraction or behavior would be less correct.

Review comments are proposals, not commands, but silence is not a disposition.
If later evidence reverses an earlier reply, post a correction and update the
PR body, decision log, tests, and stale threads so the final narrative agrees.

## Scope, authorship, and commit shape

- Outside contributors default to one coherent behavior change. Do not bundle
  unrelated cleanup without maintainer invitation.
- Maintainer-curated release bundles can be valid; keep one atomic, buildable
  commit and one proof record per task.
- Preserve partner or prior-author credit when porting work onto an Edge branch.
  State the original base and the Edge-specific modernization or fixes.
- Put dependency and lockfile commits before code that consumes the new API so
  each commit builds against its resolved dependencies.
- Use focused fixups during review and autosquash after the round, following the
  target repository workflow.
- Split risky migrations into independently useful stages when live validation
  or product decisions are not ready.

## Final PR narrative gate

Before publication or merge, make the body match the final head:

- problem, root cause, owning layer, and user-visible outcome;
- intentional behavior changes and preserved defaults;
- dependencies, merge order, configuration, and release coupling;
- exact proof plus an honest unproven matrix;
- known limitations, product decisions, and deferred work;
- CHANGELOG and visual/device evidence required by the template.

Done means the tests discriminate, evidence is labeled, review is fresh, every
material thread has a disposition, and no stale summary claims behavior the
final code does not implement.
