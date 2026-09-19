# OpenClaw Contribution Overlay

Use when the target is `openclaw/openclaw` or a close OpenClaw ecosystem contribution. This overlay carries everything OpenClaw-specific; the skill body stays repo-generic.

## Quick preflight

- Read repo `AGENTS.md`, `CLAUDE.md`, and `CONTRIBUTING.md`.
- Branch from current `openclaw/openclaw:main`; contribute through the fork unless told otherwise.
- Keep PRs surgical and user-facing.
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

Run this before starting any OpenClaw contribution:

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
- Useful contributions: rebase to latest main, fix failing tests, respond to stale reviewer comments, add missing test coverage.
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

This overlay and Crusty Contributor retain branch/PR strategy, public GitHub
writes, body updates, artifact publication, re-review requests, and contribution
bookkeeping. Receive and inspect the Proof Lab packet before publishing it.

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
