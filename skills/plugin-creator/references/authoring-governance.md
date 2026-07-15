# Skill, Plugin, Procedure, And AID Routing

Use this reference when a request says "skill", "plugin", "procedure", "playbook", "workflow", "roadmap", or "remember this for next time".

## Classification

- **Procedure**: reusable how-to instructions that do not need automatic triggering or bundled scripts. Put it in `knowledge/procedures/` and link it from the owning skill or project when relevant.
- **Skill**: triggerable agent behavior. Use when the model should load special workflow rules before acting. Source of truth is `workspace/skills/<name>/`.
- **Plugin**: runtime code, commands, tools, channel adapters, handlers, providers, or UI behavior. Put durable code in `~/projects/<unit>/` or an existing repo, not loose workspace scratch.
- **AID project unit**: multi-session work with state, decisions, blockers, or a roadmap. Use `~/projects/<unit>/` with `VISION.md`, `STATUS.md`, `LOG.md`, and optional `ROADMAP.md` per `~/projects/AGENTS.md`.
- **Upstream contribution**: use `crusty-contributor` and `~/projects/CONTRIBUTIONS_INDEX.md` in addition to any project unit.

If unclear, choose the smallest artifact that future Sean will reliably load. A procedure can graduate to a skill later; a skill can point to a procedure; a plugin can bundle or reference a skill, but they are not the same thing.

## House Rules

1. Read the existing artifact and nearby references before changing it.
2. For skills, keep `SKILL.md` lean. Move long examples, SDK notes, schemas, and historical research to `references/`.
3. For plugins, check current local OpenClaw docs/source first; public docs and old examples drift.
4. Enforce AID for every new durable project, plugin, or skill. Before creating a new artifact, check `~/projects/PROJECT_REGISTRY.md`, `~/projects/CONTRIBUTIONS_INDEX.md`, and nearby folders so work is consolidated rather than scattered. Current state lives in `STATUS.md`, append-only history in `LOG.md`, durable plans in `ROADMAP.md` only when `STATUS.md` Later has grown too large.
5. Never edit `~/projects/clawSean/skillreef` directly. SkillReef is a generated publish target; source edits happen in `workspace/skills/`.
6. Do not install, enable, restart, or repair OpenClaw, plugins, skills, or dependencies without JPop's explicit approval.
7. If the artifact affects live Gateway/channel behavior, prefer a local offline test first and use the gateway watchdog procedure for any approved restart/config path.
8. Log live skill changes in daily memory for audit.

## Mechanics Sources

- OpenClaw skill mechanics: bundled `/usr/lib/node_modules/openclaw/skills/skill-creator/SKILL.md`.
- Codex skill mechanics: Codex built-in `skill-creator`.
- Codex plugin scaffolds: Codex built-in `plugin-creator`.
- OpenClaw plugin mechanics and house gotchas: this skill.
- Development-heavy routing: `skills/development-orchestration/SKILL.md`.
- AID project docs canon: `~/projects/AGENTS.md` and public mirror `~/projects/clawSean/active-initiative-docs/`.

## Known Issues / Optimizations

- Workspace `development-orchestration` has historically had ambiguous rows pointing at bundled skills as if they were workspace paths. Say "bundled" explicitly when the skill lives under `/usr/lib/node_modules/openclaw/skills/`.
- Large skill files degrade trigger usefulness. Keep the hot path in `SKILL.md`; move recipes to references.
- Public plugin command types can lag native command internals. Verify SDK types before using built-in-only fields like typed args / `argsMenu`.
- `openclaw plugins registry --refresh` proves discovery metadata only. It is not a live runtime reload proof.
- For existing local plugins, compile TypeScript before claiming a plugin can load without runtime-output warnings.

## Done Checklist

- Artifact type is correct and smallest sufficient.
- Source-of-truth file is updated, not just chat.
- Long material lives in `references/`, `knowledge/procedures/`, or AID project docs as appropriate.
- Local validation ran or the missing validation is called out.
- No live config/service/install change happened without explicit approval.
