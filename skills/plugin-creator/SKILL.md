---
name: "openclaw-skill-plugin-lifecycle"
description: "Create, update, publish, or audit existing OpenClaw skills/plugins/procedures with Workshop lifecycle, one source, current SDK checks, and proof."
---

# OpenClaw Skill + Plugin Lifecycle

Use before creating, changing, publishing, or auditing an OpenClaw skill,
plugin/extension, reusable procedure, or durable project package.

## Classify first

Read `references/authoring-governance.md`, then choose the smallest artifact:

- **Procedure:** reusable instructions in `knowledge/procedures/`.
- **Skill:** triggerable agent behavior. Mutations go through Skill Workshop.
- **Plugin:** runtime code, commands, tools, handlers, providers, or UI.
- **Project unit:** multi-session state under `~/projects/<unit>/`.
- **Upstream contribution:** add `crusty-contributor` and the contribution board.

## Default workflow

1. Read the existing artifact and nearby references.
2. Check `~/projects/PROJECT_REGISTRY.md`,
   `~/projects/CONTRIBUTIONS_INDEX.md`, and
   `CAPABILITIES_INDEX.md` before creating another identity.
3. For a skill, create/update/revise a Workshop proposal, inspect it, and apply
   only with explicit user approval. If agent-side apply rejects a legacy skill,
   use the documented operator path:
   `openclaw skills workshop apply <proposal-id> --json`; there is no separate
   adoption step.
4. For a plugin, identify one canonical editable source and verify the current
   runtime source with `openclaw plugins list --json`.
5. Check current local OpenClaw docs/source before copying an old example.
6. Start with the smallest working behavior; add buttons/state/channel-specific
   logic only when required.
7. Verify through the real path: discover/load, command/tool invocation,
   callback routing, and relevant offline tests.
8. Update project state, capability ledger, daily audit, and generated public
   mirrors only where the owning contract requires it.

Never edit SkillReef or another generated public mirror directly.

## Skill rules

- Keep `SKILL.md` lean and move long recipes/research to `references/`.
- The applied live source is
  `~/.openclaw/workspace/skills/<name>/`.
- Workshop proposals are the mutation/review layer; applying a proposal changes
  the live source. Applying requires explicit user approval.
- Public skill outputs come only from the scrubbed publication pipeline in
  `knowledge/procedures/code-publishing.md`.

## Plugin source rules

- Prefer the runtime-loaded plugin tree when it is safe and self-contained.
- Use `~/projects/<unit>/` when a real project owns builds, tests,
  rollout state, or multiple artifacts.
- Load the project tree directly or use a deterministic build; do not maintain
  a hand-edited runtime copy and ceremonial project clone.
- Publishing does not authorize enabling, installing, changing config, or
  restarting OpenClaw.

## Minimal plugin interaction patterns

Choose the smallest verified surface:

- raw slash arguments for simple branches;
- namespaced Telegram `callback_data` plus
  `api.registerInteractiveHandler(...)` for visible inline menus;
- `presentation.buttons` when channel-agnostic rendering is proven;
- custom channel-specific callback state only for real pickers/wizards.

Telegram `ctx.respond` is an object, not a callable function. Do not invent
SDK fields such as native-only typed argument menus; inspect the installed
`OpenClawPluginCommandDefinition` first.

For minimal command plugins, button routing, manifest/build details, and known
interaction shapes, use the reference files below.

## Baseline plugin audit

1. Inventory runtime status/source with `openclaw plugins list --json`.
2. Audit only the selected custom plugin root. Do not touch bundled plugins
   unless requested.
3. Check:
   - manifest/package identity and entry paths;
   - build/test command and compiled output when required;
   - installed SDK/type compatibility;
   - fixture/mocked command, formatting, config, error, and callback behavior;
   - non-destructive `openclaw plugins inspect <id>` or doctor check when useful.
4. Patch only obvious bounded gaps.
5. Write `BASELINE_PLUGIN_AUDIT.md` in the owning plugin/project root.
6. Run the detected verification once from the parent context and state any
   missing live integration proof.

No worker may restart Gateway, mutate live config, send external messages, or
call live providers unless the user separately authorizes that action.

## Local docs and source

Resolve the current OpenClaw root rather than assuming Linux:

1. `~/.npm-global/lib/node_modules/openclaw`
2. another path returned by `command -v openclaw` / package resolution
3. project-local `node_modules/openclaw`

Relevant local docs include:

- `docs/plugins/building-plugins.md`
- `docs/plugins/sdk-entrypoints.md`
- `docs/plugins/message-presentation.md`
- `docs/tools/slash-commands.md`

Inspect installed SDK declarations under `dist/plugin-sdk/` before using an
example that may have drifted.

## Validation and activation

- Registry refresh/discovery proof is not live runtime-reload proof.
- Build TypeScript before claiming loadability when runtime output is required.
- Interactive plugins need real button visibility and callback proof before
  being called live.
- Any approved Gateway-affecting config/restart path uses
  `~/projects/gateway-watchdog/safe-apply.sh` with a dry run first.
- No install, dependency change, config mutation, plugin enablement, or service
  restart without the approval required by `USER.md`.

## References

- `references/authoring-governance.md`
- `references/openclaw-plugin-manifest-build.md`
- `references/one-shot-extension-prompt.md`
- `references/telegram-command-buttons.md`
- `references/button-branching-feasibility.md`
- `knowledge/procedures/code-publishing.md`
- `skills/development-orchestration/SKILL.md`
