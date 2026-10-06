# Skill, Plugin, Procedure, and Project Routing

Use when a request mentions a skill, plugin, procedure, playbook, workflow,
roadmap, or durable reusable behavior.

## Classification

- **Procedure:** reusable how-to in `knowledge/procedures/`.
- **Skill:** triggerable agent behavior; update through Skill Workshop.
- **Plugin:** runtime code/commands/tools/handlers/providers/UI, with one
  canonical editable source.
- **Project unit:** multi-session work in `~/projects/<unit>/` with
  `VISION.md`, `STATUS.md`, and append-only `LOG.md`.
- **Upstream contribution:** add `crusty-contributor` and
  `~/projects/CONTRIBUTIONS_INDEX.md`.

Choose the smallest artifact future the contributor will reliably load.

## House rules

1. Read the existing artifact and references before changing it.
2. Skill changes use Workshop create/update/revise, then inspect; apply only
   after explicit user approval.
3. Applied skills live under
   `~/.openclaw/workspace/skills/<name>/`; published copies are
   generated and never hand-edited.
4. Plugins keep one canonical source: a safe runtime-loaded tree or a real
   project under `~/projects/<unit>/`.
5. New durable artifacts check the project registry, contribution index, and
   capability ledger first so identities are consolidated.
6. Check current local OpenClaw docs/source before public examples.
7. No install, enablement, live config change, dependency change, or restart
   without required explicit approval.
8. Update `CAPABILITIES_INDEX.md` for meaningful availability/source/runtime/
   distribution changes; update project state separately.
9. Publish through `knowledge/procedures/code-publishing.md`.
10. Log applied skill changes in daily memory.

## Mechanics

- Workshop: skill lifecycle and live mutation.
- Bundled/Codex `skill-creator`: skill structure guidance when needed.
- Codex `plugin-creator`: Codex plugin scaffolds.
- `openclaw-skill-plugin-lifecycle`: OpenClaw skill/plugin lifecycle and house rules.
- `development-orchestration`: development-heavy execution.
- Project docs canon: `~/projects/AGENTS.md`.

## Done

- Correct artifact type and one canonical source.
- Proposal/approval lifecycle satisfied for skills.
- Local proof run or missing proof named.
- State/ledger/daily audit updated where applicable.
- No generated mirror hand-edited.
- No live activation or restart smuggled into authoring work.
