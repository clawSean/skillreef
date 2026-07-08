---
name: "crusty-contributor"
description: "Public-safe upstream contribution workflow for any GitHub repo: redundancy checks, issues, PRs, proof, CI/review follow-through."
---

# Crusty Contributor

A public-safe upstream contribution workflow for issues, PRs, CI/review follow-up, and contribution hygiene — for **any** GitHub repo that is not ours.

## Boundary with development-orchestration

`development-orchestration` is the front door: it decides whether this skill applies and owns generic project state routing (TaskFlow, project floor files, legacy `PROJECT_PROGRESS.md`, registry). This skill owns contribution execution, public-safe GitHub hygiene, and contribution status bookkeeping in `~/projects/CONTRIBUTIONS_INDEX.md`.

## Repo Overlays

Before starting, check `references/` for a repo-specific overlay and load it if present. **OpenClaw / close ecosystem repos → `references/openclaw.md` (mandatory).** Overlays and repo-native guidance win over this generic body. New frequent-target repos get their own `references/<repo>.md` — the body stays generic.

⚠️ **Proof tripwire:** for OpenClaw PRs, proof of real behavior is a first-class deliverable, not a final comment — the overlay routes you to `references/openclaw-proof-runbook.md`. Do not claim a PR is ready without passing that gate.

## 0. Redundancy Check (do this before any work)

**Before writing a single line of code or filing anything**, confirm the problem is not already solved or actively being worked:

1. **Search closed issues** — `gh search issues '<symptom keywords>' --repo <owner/repo> --state closed --limit 10`
2. **Search open PRs** — `gh pr list --repo <owner/repo> --search '<keywords>' --state open`
3. **Search closed PRs** — `gh pr list --repo <owner/repo> --search '<keywords>' --state closed`
4. **Check if the bug exists in the latest release** — confirm the symptom still reproduces on current upstream, not just the installed version.
5. **Check the changelog/release notes** — scan `CHANGELOG.md` or recent releases for a fix that shipped after the version where you hit the bug.

Decision tree:

| What you find | Action |
|---|---|
| Already fixed in a newer release | Upgrade and close the loop; no contribution needed |
| Closed issue/PR that fixed it | Confirm fix is in latest; if backport needed, say so |
| Open PR that addresses it | Read it. Green/ready → cheer it on. Stale, failing, or needs rebase → **contribute to that PR instead of opening a new one** |
| Open issue, no PR yet | Reference the issue in your PR |
| Nothing found | Proceed with contribution |

If an existing open PR already covers the fix:
- Don't open a duplicate PR.
- Monitor it. If it goes stale, offer to help: rebase, fix failing tests, add missing tests, address review feedback.
- If the original author is unresponsive and the PR is abandoned, note that before opening a superseding PR.

If our PR already exists and a competing fix appears:
- Compare merge likelihood before doing more branch maintenance.
- Prefer the official upstream outcome over keeping our branch alive.
- Keep or reshape our PR only when it can become clearly better: safer, more accurate, better scoped, better proven, or easier to merge.
- Closing one of our PRs is never this skill's call: PR close/freeze policy lives in the `clawloop` skill (freeze + notify; closing is always JPop's decision).
- Record useful unblocking/triage credit locally even when the final upstream patch is not ours.
- If no maintainer signal arrives after roughly 2-3 weeks on a clean/actionable PR, downgrade to background watch and spend active effort on newer higher-odds work.
- In public comments, frame overlap as collaboration or consolidation toward the best upstream fix. Avoid "our PR will win" language.

If the user asks for strategy, profile, docs, or second-opinion review:
- Return the strategy recommendation first.
- Do not turn the review into external GitHub action unless the user explicitly asked for execution too.
- If the review uncovers an urgent live blocker, call it out as a recommended next action before acting externally.

## 1. Read the Repo First

Before editing or posting, identify the target repo, issue/PR, branch, and desired outcome. Then read repo-native guidance:

- `AGENTS.md`, `CLAUDE.md`, `.cursor/rules/`, `.cursorrules`
- `CONTRIBUTING.md`, `SECURITY.md`, `SUPPORT.md`, `CODE_OF_CONDUCT.md`

The repo's most specific guidance wins over this skill. If no guidance exists, match nearby style and be conservative.

Before choosing an implementation, also inspect the local convention history for the touched area:

- Read nearby files and tests, not just the failing line.
- Search recent merged PRs touching the same plugin/module/API path.
- Search issue/PR discussion for prior rejected approaches or maintainer preferences.
- Ask the coding agent explicitly: "Does this match the project's conventions, and is this the most robust fix?"

Maintainers are more likely to reject AI-assisted PRs that are technically plausible but convention-breaking, fragile, or one-line symptom patches. Treat convention fit and robustness as merge-readiness requirements, not polish.

## 2. Public Safety

Before anything leaves the machine as an issue, PR, comment, gist, screenshot, or log paste:

- Strip secrets, tokens, cookies, private keys, internal endpoints, and credentials.
- Remove private chat metadata, personal memory, relationship context, customer/company details, and local operational lore.
- Generalize local-only paths, hostnames, account IDs, project names, and machine-specific details unless needed to reproduce and explicitly approved.
- Preserve exact public error messages, stack traces, versions, commands, file names, and repo paths when they matter.
- Litmus test: a stranger should understand the report without learning who JPop is, where this agent runs, or what private systems exist.

Ask before making reputationally sensitive or irreversible external posts.

## 3. Issue vs PR

| Situation | Default action |
|---|---|
| Narrow bug with clear root cause | PR directly, reference symptom/issue |
| Docs typo, small docs correction | PR directly |
| Missing handler/route for already-declared behavior | PR directly |
| Broad feature/API/architecture change | Issue/discussion first |
| Security/policy-sensitive report | Follow repo security policy first |
| Root cause unclear | Issue first, or investigate before PR |

When unsure, file the issue first. Small, sharp PRs beat broad speculative rewrites.

### Positioning for Merge (maintainer attractiveness)

How work is framed changes merge odds as much as what the code does. Apply at PR creation, and re-apply whenever a PR stalls (proven on #51762, 2026-07-04):

- **Anchor to a LIVE issue.** A PR whose canonical issue is closed is an orphan. Stale-bot closure ("closed due to inactivity" / `not_planned` by a bot) is NOT a maintainer rejection — but don't argue that; instead search for a newer OPEN issue tracking the same problem family and re-anchor (`Closes #N`) there. High-priority/high-rating open issues are the best anchors.
- **Bug frame beats feature frame.** Maintainers merge fixes for open bugs far more readily than they sponsor new product surface. If feature-shaped work honestly fixes an open bug, retitle and re-body it as `fix:` for that bug and let the feature framing go.
- **Zero-new-surface bias.** New config keys, env vars, CLI flags, and API contracts are the #1 sponsorship objection. Prefer making an EXISTING mechanism work correctly everywhere over adding a parallel one. When new surface is genuinely wanted, split it into a separate follow-up draft PR so the fix PR carries none of it.
- **Ride accepted direction.** Search merged PRs near your change: if upstream already merged a sibling (partial acceptance of the same direction), reuse its helpers and patterns and frame yours as the continuation/completion — not a competing design.
- **Recruit the demand.** The strongest maintainer pull is an affected user commenting "this fixes it on our production deployment." Ask the anchor issue's author (and other affected commenters) to test your branch. Draft such comments for JPop review before posting.
- **Professional title.** No jokes, memes, or emoji in the PR title — maintainers triage by scanning titles, and a joke title reads hobby-grade. Personality goes in the sign-off, not the subject line.
- **Answer risk labels explicitly.** If the repo applies merge-risk/impact labels, the PR body gets one short mitigation subsection per label. An unanswered risk label is a standing reason not to merge.
- **Re-anchor check on every stalled PR.** The landscape moves: issues open and close, partial fixes merge, competitors appear. For any PR stalled >2 weeks, re-run the redundancy check in reverse — look for NEW open issues your work could close and NEW merged PRs to build on — before spending another rebase on the old framing.

## 4. Branch and Diff Hygiene

- Branch from current upstream default branch unless resuming an existing PR.
- Do not branch from a stale fork default branch blindly.
- Keep one logical change per PR.
- Avoid drive-by cleanup, unrelated formatting churn, and unrelated generated-file updates.
- Confirm the real source file, not only generated `dist`/build output.
- Inspect `git status`, `git diff`, and `git diff <base>...HEAD --stat` before committing or pushing.
- Use clean, conventional-ish commit messages.

## 5. Implement and Validate

- Follow existing repo patterns for storage, routing, errors, and tests.
- Prefer root-cause fixes over narrow symptom patches; call out why the chosen shape is robust.
- Add or update focused tests for changed behavior.
- For user-facing behavior/API/docs changes, check docs and release-note/changelog expectations.
- Treat missing required release-note or changelog context as a merge-readiness blocker, but follow the target repo's current policy exactly.

### Pre-Push Regression Gate

Run this as a short near-miss regression pass over the final diff when the patch changes behavior in an area where near-miss behavior matters.

Activate the gate for changes involving:

- authorization, permissions, trust, secrets, or security boundaries
- routing, parsing, command detection, channel ingress, runtime metadata, or event classification
- user-visible behavior where a false positive, false negative, or wrong-session route would be harmful
- shared helpers, cross-channel contracts, or framework-level behavior

Skip or keep it to a one-line N/A for:

- docs-only, copy-only, typo, README, comment-only, or changelog/body-only changes
- formatting-only or generated-output-only changes when source behavior is untouched
- test-only changes that do not alter behavior
- tiny local bugfixes with no sibling implementation, parser predicate, or downstream semantic fact

Timebox the initial gate to about 5-10 minutes. If no sibling or meaningful near-miss exists, record that and move on. If the gate exposes real ambiguity or risk, spend more time — it has already paid for itself.

Ask and answer these questions from the code, not vibes:

- **Positive path:** Is there a focused test proving the intended new behavior?
- **Negative path:** Is there a focused test proving the closest near-miss does *not* get the new behavior?
- **Sibling parity:** Did I compare the closest existing sibling implementation and match its split points, names, and contracts?
- **Predicate contract:** Am I using a broad probe, heuristic, or false-positive-tolerant helper to create a narrower semantic fact? If yes, split the broad probe from the exact detector.
- **Downstream meaning:** What changes once this context/metadata/authorization fact is set? Add a regression for any accidental downstream classification.

Common trap: one helper may be valid for cheap authorization probing because false positives are harmless, while another exact helper is required before declaring a structured command/event/security fact. Never collapse those without checking helper comments and sibling callers.

Repo overlays may add repo-specific regression requirements (OpenClaw's command/channel rules live in `references/openclaw.md`).

### Proof and Validation Gates

Minimum gates before claiming success:

- Formatter or `git diff --check` for touched files.
- Targeted tests/typechecks/lints for the touched area.
- Pre-Push Regression Gate above when activated, with the negative/sibling result recorded in notes or PR body for non-trivial behavior changes.
- Heavier full checks when practical or when touching shared infrastructure.
- If full checks are too heavy or locally blocked, state which targeted gates passed, name the exact local blocker, and follow PR CI until resolved.
- Repo overlay proof requirements (e.g. OpenClaw's proof runbook and pre-PR wrapper) when the target repo has them.

Do not say a branch is "ready" or "merge-ready" immediately after upload when an expected repo bot/reviewer has not looked yet. Say "PR opened; local gates passed; awaiting first bot/review pass." Upgrade the status only after review/CI confirms or after you have triaged failures.

## 6. PR Body

Use `references/pr-template.md` when helpful. Strong PR body shape:

- Problem / user-visible impact
- Root cause
- What changed
- What did not change / scope boundaries
- Tests run
- Related issue(s)
- AI assistance disclosure when expected by repo norms
- Maintainer-fit evidence when useful: nearby convention followed, prior PR/issue history checked, and why this is not a fragile workaround
- Optional reasoning/proof artifact: attach or link a sanitized agent transcript/summary when the repo/community values seeing the investigation trail

End user-facing status with the full issue/PR URL when working on an issue/PR.

## 7. Follow Through and Bookkeeping

- Watch CI and reviews until the PR is merge-ready or explicitly blocked.
- Separate failures caused by the PR from upstream flakes, infra failures, or unrelated `main` breakage.
- Fix only diff-caused failures on the PR branch; document evidence for unrelated failures.
- Respond to review feedback promptly with the smallest satisfying change.
- Rebase when needed, but avoid unnecessary force-push churn during review.

**This skill owns contribution status bookkeeping:**

- Update `~/projects/CONTRIBUTIONS_INDEX.md` when a contribution changes state, a PR opens/closes/merges, or the next action changes.
- Keep or update the relevant project state surface (`STATUS.md`/`LOG.md` for migrated units, legacy `PROJECT_PROGRESS.md` otherwise) for multi-session contribution tracks.
- Capture durable workflow lessons in the matching `knowledge/procedures/` playbook.

## References

- `references/openclaw.md` — OpenClaw-specific contribution overlay (preflight, proof gates, release-note policy, command/channel regression rules).
- `references/openclaw-proof-runbook.md` — OpenClaw proof creation, Mantis/ClawSweeper acceptance, fresh-head proof refresh, label decoding, example patterns.
- `references/pr-template.md` — copyable PR body/checklist.
