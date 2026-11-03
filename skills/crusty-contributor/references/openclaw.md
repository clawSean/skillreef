# OpenClaw Contribution Overlay
Use when the target is `openclaw/openclaw` or a close OpenClaw ecosystem contribution. This overlay carries everything OpenClaw-specific; the skill body stays repo-generic.
## Quick preflight
- Read repo `AGENTS.md`, `CLAUDE.md`, and `CONTRIBUTING.md`.
- Branch from current `openclaw/openclaw:main`; contribute through the fork unless told otherwise.
- Keep PRs surgical and user-facing.
- Prepare an honest demand case; classify each signal as independent demand,
  self-reproduction, adjacent accepted direction, operational impact, or
  standards/vendor pressure. A personal/workspace skill or channel-specific
  preference may justify a narrow affected-channel fix, but not, alone, a
  shared/public API, cross-channel behavior, or broad architecture. Default to the narrowest current owner.
  Expand only for architectural necessity, independent demand, or accepted upstream direction.
  Lack of prior external demand does not block a cutting-edge contribution, but
  unqualified self-filed issues do not count as sponsorship.
- Freeze one first slice before implementation: user-visible behavior, narrowest
  owner, non-goals, and projected diff. More than 150 changed lines and five files,
  durability/schema/migration, replay/restart, multiple channels, or shared owners
  are split triggers; exceed only for named safety/correctness needs.
- A maintainer request to split or start small is a hard reset: branch from current `main`, rederive only the named slice, use the old branch as evidence—not architecture, and publish only when the diff matches the frozen slice or the maintainer explicitly accepts wider scope.
- Lead every non-trivial PR body with the reviewer-first `Merge Brief` from
  `references/pr-template.md`. Keep it to roughly ten scannable lines covering
  problem, why now/demand signal, value, smallest complete fix, scope, risk,
  proof, non-goals, and one maintainer ask. Put forensic receipts and long test
  matrices below the brief or in collapsed/linkable artifacts. A maintainer
  should be able to orient and decide what to inspect next in under one minute.
- Insert the brief above OpenClaw's existing body structure. Preserve the exact
  `## What Problem This Solves` and `## Evidence` headings; the brief supplements,
  never replaces, required sections. A body write is incomplete until the fresh
  PR context and evidence gate passes.
- Read the current upstream `.agents/skills/openclaw-testing/SKILL.md` before choosing test commands; read `.agents/skills/openclaw-qa-testing/SKILL.md`, `.agents/skills/crabbox/SKILL.md`, or the relevant proof skill only when that surface needs it.
- Use targeted tests first. Do not preserve historical command strings as contracts when current repo guidance has a cheaper or safer lane.
- For routing/auth/command/channel PRs, run the Pre-Push Regression Gate (skill body §5) plus the OpenClaw-specific rules below before opening or updating the PR.
- Update `~/projects/CONTRIBUTIONS_INDEX.md` and relevant `PROJECT_PROGRESS.md` for important PRs.
## Deterministic maintenance preflight
Before every conflict-repair or maintenance push, run the canonical wrapper
against the maintenance epoch's immutable base:
```bash
~/.openclaw/workspace/scripts/openclaw-pre-pr.sh \
  --repo "$WORKTREE" \
  --base "$BASE_SHA" \
  --no-fetch \
  --epoch-id "$EPOCH_ID" \
  --receipt "$RECEIPT_PATH"
```
- The coordinator fetches `main` once and distributes the resulting 40-character
  `BASE_SHA`; workers never fetch or substitute a newer base inside the epoch.
- The wrapper delegates lane selection to the checkout's current
  `scripts/check-changed.mjs`; do not duplicate the hosted CI matrix in prompts.
- The receipt must bind epoch, base, head, merge tree, selected lanes,
  dependency state, gate outcomes, timings, and exit status. A head change makes
  the receipt stale.
- Repository-policy checks are deterministic. Use an LLM only for conflict
  intent, risk review, or ambiguous hosted-CI attribution. Proof Lab separately
  owns exact-head runtime behavior evidence.
- A nonzero gate blocks publication. Name external or dependency blockers; do
  not replace a failed deterministic gate with reviewer confidence.
## Canonical guidance
Repo files are authoritative:
- `AGENTS.md` — agent/developer workflow, tests, changelog, git rules.
- `CLAUDE.md` — Claude-specific mirror of repo guidance.
- `CONTRIBUTING.md` — human contribution expectations.
Local workspace references:
- `knowledge/procedures/openclaw-upstream-contribution-playbook.md` — detailed workflow and lessons.
- `knowledge/procedures/openclaw-taskflow-issue-intake.md` — manual TaskFlow-style funnel for turning fresh OpenClaw issues into shortlisted PR candidates; use before this overlay, not instead of it.
- `~/projects/CONTRIBUTIONS_INDEX.md` — active PR/issue board.
- Relevant project `PROJECT_PROGRESS.md` — live context for longer contribution tracks.
## Redundancy check (OpenClaw-specific)
This is the first per-PR action. Run it before code repair, dependency work,
proof creation, or body/public mutation. If current main or a merged PR already
removes the user gap, stop and record a closure recommendation.
```bash
# Is the symptom already fixed in the latest release?
gh release list --repo openclaw/openclaw --limit 5
# Then check CHANGELOG.md for your symptom keywords

# Closed issues with similar symptom
gh search issues '<keywords>' --repo openclaw/openclaw --state closed --limit 10

# Open PRs that might already fix it
gh pr list --repo openclaw/openclaw --search '<keywords>' --state open

# Closed PRs (merged fixes you might have missed)
gh pr list --repo openclaw/openclaw --search '<keywords>' --state closed --limit 10
```
If an **open PR already targets the same bug**:
- Don't open a new PR — contribute to the existing one.
- Useful contributions: rebase when conflicts or a maintainer request require it, fix failing tests, respond to stale reviewer comments, add missing test coverage. Do not chase a moving upstream head.
- If the PR is abandoned and the author is unresponsive (>2 weeks, no activity), note this explicitly before superseding.

If **our PR is stale, duplicated, or has a stronger competing PR**:
- Read the newest issue/PR comments, ClawSweeper review, linked PRs, recently merged adjacent work, and current-main source before rebasing or repairing.
- Decide whether the goal is still to land our branch or to help the official upstream fix land.
- Keep our branch only if it can be made clearly preferable on maintainer terms: narrower root cause, safer compatibility posture, stronger proof, cleaner CI, or better docs/product wording.
- Freeze our branch and recommend closure when another PR already merged, has stronger maintainer signal, or is the canonical root-cause shape; actual closure remains user-only under the `clawloop` policy.
- Preserve the lesson/status in `~/projects/CONTRIBUTIONS_INDEX.md` or the project notes so useful triage still counts.
- If a clean/actionable PR gets no maintainer signal for roughly 2-3 weeks, move it to background watch unless new evidence raises merge probability.
- When commenting publicly on overlap, offer consolidation/help and avoid language about beating, winning, or outcompeting another contributor.

### Close-reason audit discipline

When auditing old the author/reviewer OpenClaw PRs, keep the factual packet separate from the lesson synthesis:

- Build or read the lossless GitHub-backed audit artifact first: PR metadata, timeline close/merge events, issue comments, review bodies, and review comments.
- Do not infer the root cause from labels or local project notes alone; GitHub PRs do not expose a structured close-reason field.
- Do not update this overlay with takeaway lessons until the reviewer has reviewed the factual packet, optional model reviews have converged, and the agreed causes are explicit.
- Before deleting any local worktree, preserve local-only proof logs, draft bodies, screenshots, transcripts, or untracked artifacts that are not already in GitHub comments, project logs, or the audit artifact.

When doing a strategy or second-opinion pass, stop at recommendations first. External PR comments, pushes, or closes need explicit execution intent from the user or a prior still-active request.

If the **bug is fixed in a newer OpenClaw release** than what's installed:
- No contribution needed — just upgrade.
- Update `~/projects/CONTRIBUTIONS_INDEX.md` to close the relevant track.

## Required habits

- Branch from latest upstream `main`, not stale fork `main`.
- Use the fork remote for pushes and PRs unless direct upstream access is explicitly intended.
- Keep PR scope narrow: one bug, handler, route, doc gap, or behavior correction.
- Re-run the merge brief whenever the head, proof state, requested decision, or
  demand evidence materially changes; stale sales copy is a merge-readiness bug.
- After every head or body mutation, reread the edited-in-place review comment
  and its markers. Bind readiness to the exact head, current body/source revision,
  and latest review source revision; never reuse cached findings.
- Process each PR in order: live relevance/overlap -> preserve body template ->
  repair and prove only if relevant -> refresh brief -> context/evidence gate ->
  public write -> exact readback -> fresh rolling-review readback.
- Treat OpenClaw's official `20`-open-PR-per-author cap as a safety limit, never
  an output target. Mirror the enforcement query: count `is:pr is:open
  author:<login>` separately for each author. Draft PRs count; GitHub issues do
  not. Our reviewer-cost controls remain intentionally stricter: At 12 or more,
  require a written portfolio-rank check; At 15 or more, keep new work
  local/candidate-first unless the user explicitly authorizes a different
  bounded exception. A draft does not create capacity.
- Prefer source edits over generated `dist` edits unless generated files are intentionally part of repo workflow.
- Add focused tests near existing tests for the touched package/extension.
- Use `pnpm` when `pnpm-lock.yaml` is present.
- Run targeted Vitest configs directly when wrapper filtering is awkward.
- For docs/changelog-only changes, run `git diff --check`, the repo-required docs checks, and the Docs truth gate below; run runtime/build checks only if behavior changed.

## Docs truth gate

For OpenClaw docs changes, passing automated docs checks is necessary but not sufficient:

- Read `docs/AGENTS.md` and any more-specific guidance for every touched subtree; enforce literal conventions, not just whether the renderer accepts the text. In Mintlify docs, internal section links—including same-page references—use canonical root-relative `/route#anchor` form rather than bare `#anchor`.
- Treat every workaround or API instruction as an operational contract. Verify and state the actor, credential or token, required membership/permission, target, and effect. Do not present a human UI/CLI path and an API path as interchangeable when caller prerequisites differ.
- Trace external-platform claims to current source plus primary vendor docs or reproducible evidence. Separate what OpenClaw does from what the platform permits, and narrow claims to the evidence.
- On the exact final head, run the required docs checks and `git diff --check`, regenerate/check derived docs, then reread the rendered paragraph specifically for who-can-do-what ambiguity.

## Command/channel regression rules

For OpenClaw command/channel PRs specifically (adapt for other repos' routing/event/metadata contracts):

- Use broad command-detection probes only to decide whether command authorization should be computed.
- Use exact control-command detection before attaching `command: { kind: "text-slash" }` or equivalent command-turn metadata.
- Add at least one negative inline-token regression, such as a normal message containing a path or incidental slash-like token.
- Compare at least two nearby text-capable channels when available, then note the chosen analogue in the PR body or local notes.

## Proof Creation Gate

For OpenClaw behavior proof, load `openclaw-proof-lab`. It owns proof
classification, state, route selection, execution, artifact inspection,
redaction, current-head packets, and the optional proof-subagent contract.

Load it whenever the PR changes user-visible behavior, routing, delivery,
config/startup/update behavior, auth/security, provider behavior, native apps,
persistent state, or another surface whose real behavior affects review. Also
load it whenever a reviewer, bot, label, or head change creates proof debt.

Crusty retains public writes. Before create, ready, or a behavior-changing push,
inspect the candidate-head packet and run `scripts/proof-publication-gate.sh`.
Publish non-draft with an honest proof-debt disclosure when proof is planned,
attempted, externally blocked, or stale. Hold only when a repository rule,
maintainer request, or concrete safety boundary explicitly makes proof a
pre-publication requirement. Later proof clears debt; it is not what makes the
contribution exist.

`Exact head` means the contribution head SHA exercised by the evidence, not the
moving tip of upstream `main`. Upstream movement alone never invalidates proof.
When the contribution head changes, compare the effective patch and affected
dependencies: carry the receipt forward after equivalence checks for an
ancestry-only rebase, and rerun only the proof affected by code, conflict
resolution, generated output, or dependency changes.

Proof Lab's routing reference owns current ClawPop, Crabbox, hosted, Mantis,
macOS, iOS Simulator, and pre-PR-wrapper status. Do not duplicate those
machine or rollout facts here.

## Release-note rule

Follow current repo `AGENTS.md`. As of the current OpenClaw guidance, normal PRs should **not** edit `CHANGELOG.md`; release generation owns that file.

For user-facing `fix` / `feat` / `perf` PRs, put release-note context in the PR body, squash message, or direct commit instead:

- behavior change
- touched surface
- issue/PR refs
- credited human author/reporter when useful

Treat missing required release-note context as a merge-readiness blocker. Only edit `CHANGELOG.md` when current repo guidance or an explicit release/changelog task asks for it.

## PR status triage

Merge-readiness means:

- focused diff
- targeted local validation done
- required release-note/docs context included
- CI failures understood
- review feedback handled
- branch current enough with `main`

When CI is red:

1. Identify the failing check/job/log.
2. Decide whether the failure is caused by the diff, upstream/main, infra, or a flake.
3. Fix only diff-caused failures on the PR branch.
4. If unrelated, document evidence concisely instead of churning code.

When review requests changes:

1. Apply the smallest satisfying fix.
2. Re-run the smallest meaningful gate.
3. Push and summarize what changed.

## Local bookkeeping

For important contribution work:

- Update `~/projects/CONTRIBUTIONS_INDEX.md` when a project changes state, a PR opens/closes, or next action changes.
- Keep or update a local `PROJECT_PROGRESS.md` for multi-session contribution tracks.
- Capture durable lessons in `knowledge/procedures/openclaw-upstream-contribution-playbook.md` or `memory/lessons/openclaw-operations.md` when the workflow changes.
