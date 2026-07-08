# crusty-contributor

An OpenClaw skill that turns an agent into a disciplined upstream contributor for **any** GitHub repo that isn't yours — the public-safe sibling of internal contribution tooling.

It codifies the boring-but-decisive parts of getting a change merged: checking for redundancy before you write anything, framing the PR so a maintainer wants to merge it, proving the change actually works, and following through on CI and review instead of ghosting the branch.

This is not a code generator. It's a workflow harness: how to scope a contribution, how to position it for merge, what proof to attach, and how to keep contribution status honest.

## When it shines

- Opening issues/PRs against a third-party repo where merge-positioning matters
- Deciding whether a change is even worth submitting (redundancy / competing-PR checks)
- Attaching real proof to a PR instead of "trust me, it works"
- Staying on top of CI failures and review comments until the thing lands
- Keeping a truthful record of what's open, merged, or abandoned

## What it includes

- `SKILL.md` — the workflow, decision gates, and merge-positioning doctrine
- `references/openclaw.md` — OpenClaw-specific contribution overlay (deltas only)
- `references/openclaw-proof-runbook.md` — the mandatory proof gate + label decoder with real PR examples
- `references/pr-template.md` — starting PR structure (swap sections to match a repo's enforced gates)

## Boundary

`development-orchestration` is the front door — it decides whether this skill even applies and owns generic project/state routing. `crusty-contributor` owns contribution *execution* and GitHub hygiene. For contributions to your **own** repos, use your internal flow, not this one.

## Quickstart

There's no binary to run — load `SKILL.md` when an agent is about to contribute upstream, and follow the gates in order:

1. **Redundancy check** — is this already open / already solved? If so, stop.
2. **Frame** — bug-frame over feature-frame; bias toward zero new surface.
3. **Prove** — attach evidence per `references/openclaw-proof-runbook.md`.
4. **Follow through** — clear CI, answer review, re-anchor on stall.
