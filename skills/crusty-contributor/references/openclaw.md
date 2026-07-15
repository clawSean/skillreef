# OpenClaw Contribution Overlay

Use when the target is `openclaw/openclaw` or a close OpenClaw ecosystem contribution. This overlay carries everything OpenClaw-specific; the skill body stays repo-generic.

## Quick preflight

- Read repo `AGENTS.md`, `CLAUDE.md`, and `CONTRIBUTING.md`.
- Branch from current `openclaw/openclaw:main`; contribute through the fork unless told otherwise.
- Keep PRs surgical and user-facing.
- Use targeted tests first, then `pnpm check:changed` or CI when appropriate.
- For routing/auth/command/channel PRs, run the Pre-Push Regression Gate (skill body §5) plus the OpenClaw-specific rules below before opening or updating the PR.
- Update `~/projects/CONTRIBUTIONS_INDEX.md` and relevant `PROJECT_PROGRESS.md` for important PRs.

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
- Close our branch when another PR already merged, has stronger maintainer signal, or is the canonical root-cause shape.
- Preserve the lesson/status in `~/projects/CONTRIBUTIONS_INDEX.md` or the project notes so useful triage still counts.
- If a clean/actionable PR gets no maintainer signal for roughly 2-3 weeks, move it to background watch unless new evidence raises merge probability.
- When commenting publicly on overlap, offer consolidation/help and avoid language about beating, winning, or outcompeting another contributor.

### Close-reason audit discipline

When auditing old Sean/JPop OpenClaw PRs, keep the factual packet separate from the lesson synthesis:

- Build or read the lossless GitHub-backed audit artifact first: PR metadata, timeline close/merge events, issue comments, review bodies, and review comments.
- Do not infer the root cause from labels or local project notes alone; GitHub PRs do not expose a structured close-reason field.
- Do not update this overlay with takeaway lessons until JPop has reviewed the factual packet, optional model reviews have converged, and the agreed causes are explicit.
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
- For docs/changelog-only changes, `git diff --check` plus relevant formatter/docs sanity is usually enough; escalate only if runtime/build behavior changed.

## Command/channel regression rules

For OpenClaw command/channel PRs specifically (adapt for other repos' routing/event/metadata contracts):

- Use broad command-detection probes only to decide whether command authorization should be computed.
- Use exact control-command detection before attaching `command: { kind: "text-slash" }` or equivalent command-turn metadata.
- Add at least one negative inline-token regression, such as a normal message containing a path or incidental slash-like token.
- Compare at least two nearby text-capable channels when available, then note the chosen analogue in the PR body or local notes.

## Proof Creation Gate

For `openclaw/openclaw` PRs, treat proof as a first-class deliverable, not a final comment.
Read `references/openclaw-proof-runbook.md` whenever any of these are true:

- the PR changes user-visible behavior, routing, channel delivery, config/startup/upgrade behavior, auth/security boundaries, provider/API behavior, node-host behavior, or cross-session state
- ClawSweeper, Mantis, Codex, Barnacle, or a maintainer asks for proof, context, evidence, screenshots, recordings, live observations, or real behavior proof
- the PR has or needs labels such as `proof: supplied`, `proof: sufficient`, `proof: 📸 screenshot`, `proof: 🎥 video`, `status: 📣 needs proof`, `status: ⏳ waiting on author`, `mantis: telegram-visible-proof`, `clawsweeper:automerge`, `clawsweeper:merge-ready`, or any `clawsweeper:needs-*` label
- the branch was rebased, amended, or force-pushed after proof was posted

Before asking for re-review, produce a fresh-head proof packet: current head SHA, changed surface, focused tests, live/real-environment proof when needed, negative/sibling checks, known gaps, and whether any red CI is branch-caused or unrelated. Update the PR body Evidence section for durable context; use comments only for short re-review notes or artifact links.

### Pre-PR wrapper

For OpenClaw upstream PR work from Sean's workspace, run the deterministic pre-PR wrapper before every push (initial submission, rebases, and CI-fix pushes alike; if a run is genuinely impossible — e.g. unhydrated worktree — say so explicitly in the PR notes instead of silently skipping):

```bash
~/.openclaw/workspace/scripts/openclaw-pre-pr.sh --repo <openclaw-worktree>
```

Use `--plan-only` first for heavy or uncertain branches, and add `--pr-body <path>` when a draft PR body exists so the upstream real-behavior proof policy is checked locally. This wrapper delegates to upstream OpenClaw scripts and is the preferred enforcement entrypoint.

#### Deferred mirror tooling (decision 2026-07-04, revisit on trigger)

The wrapper's OpenGrep and workflow-sanity mirror lanes are deliberately **not installed** on the VPS — they self-skip with a printed notice and the GitHub-hosted lanes remain canonical. Evidence at decision time: zero OpenGrep failures across our entire PR history, and zero workflow-touching PRs ever authored, so the mirrors would never have fired. Worst case without them is one extra push + re-review cycle after a red hosted lane.

Install triggers — set up the same day any of these become true:

- a PR of ours actually fails hosted OpenGrep → install `opengrep`
- we start authoring `.github/workflows/`, pre-commit, or zizmor changes → install `actionlint` + `pre-commit`
- we take on security-pattern-heavy work where a post-push security-lint surprise is expensive → install `opengrep` proactively

The wrapper prints when it skips a mirror, so there is no silent gap — this note exists so "should we install it?" isn't re-litigated from scratch each time.

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
