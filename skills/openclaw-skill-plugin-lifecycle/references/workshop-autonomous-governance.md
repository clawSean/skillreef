# Autonomous Workshop Governance

## Why an adapter is needed

OpenClaw's autonomous Skill Workshop reviews can run outside the foreground
bootstrap. A lifecycle-skill pointer in `AGENTS.md` therefore does not prove
that a detached review received the skill or could inspect skills owned outside
Workshop.

Use a thin runtime adapter for that boundary. It should read the canonical
lifecycle `SKILL.md` for each targeted review, build a compact owner index from
the current external skill tree, and add both to the review's system context.
The lifecycle skill remains the single policy owner.

## Required coverage

- detached per-turn review in Workshop `propose` mode;
- detached per-turn maintenance in Workshop `auto` mode;
- the system-owned weekly collection review used by `auto` mode.

Do not target ordinary foreground turns. Normal skill routing continues to own
explicit authoring and foreground repair.

## Runtime contract

- Classify reviews by stable runtime identity, not natural-language prompt
  matching.
- Read the lifecycle source and owner index dynamically; do not embed a second
  policy copy in adapter code.
- Fail closed before model inference when a targeted review lacks the injected
  governance marker.
- Leave unrelated turns untouched.
- Re-run the contract tests after OpenClaw upgrades because run and cron
  identities are host contracts.

A compact reference implementation is
[`workshop-governance-context`](https://github.com/EdgeClaws/openclaw-workshop-governance).
It covers the three lanes with prompt-build and pre-run hooks while keeping the
policy in this skill.

## What this does not solve

Governance awareness is not edit provenance. The adapter does not create Git
commits, rollback snapshots, or recovery points. Treat those as independent
gates before enabling unattended `auto` edits.
