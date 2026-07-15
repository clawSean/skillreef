---
name: plugin-creator-openclaw
description: "Create, update, audit, or route OpenClaw plugins, skills, and durable procedures; enforce AID project docs, house skill/plugin rules, SDK checks, and real command-path verification."
---

# OpenClaw Skill + Plugin Creator

Use this skill before touching an OpenClaw skill, plugin/extension, or reusable procedure doc. It is the house routing layer: decide whether the artifact is a procedure, skill, plugin, project unit, or upstream contribution; then load the narrower mechanics skill or reference.

## Fast Path

For any skill/plugin/procedure routing decision, read `references/authoring-governance.md`.

For a minimal chat slash-command plugin, read `references/one-shot-extension-prompt.md` and adapt the prompt/template to the target plugin.

For Telegram or button branching, read `references/telegram-command-buttons.md` before choosing an implementation pattern. For feasibility and a minimal two-button branching skeleton, read `references/button-branching-feasibility.md`. Remember: Telegram interactive `ctx.respond` is an object (`reply`, `editMessage`, `editButtons`, `clearButtons`, `deleteMessage`), not a callable function.

For OpenClaw plugin manifest/build details, read `references/openclaw-plugin-manifest-build.md`.

## Default Workflow

1. **Classify the artifact first.** Procedure for reusable instructions; skill for triggerable agent behavior; plugin for runtime/API/UI/tool behavior; AID project unit for multi-session work with state.
2. **Load the mechanics source.** Bundled `skill-creator` for SKILL.md mechanics, Codex's built-in `plugin-creator` for Codex plugins, this skill for OpenClaw plugins and house rules, `development-orchestration` once real coding/project execution starts.
3. **Check current SDK/docs before examples.** Inspect local OpenClaw docs/source before assuming stale examples are valid.
4. **Start boring:** make the smallest working command/skill/procedure before adding buttons, state, or channel-specific behavior.
5. **Use the smallest plugin interaction pattern that works:**
   - raw slash args for simple command branches
   - `channelData.telegram.buttons` with namespaced `callback_data` + `api.registerInteractiveHandler(...)` for Telegram-first command menus that must visibly render inline buttons
   - `presentation.buttons` + `api.registerInteractiveHandler(...)` when channel-agnostic rendering is verified for the target delivery path
   - custom channel-specific callback logic only for stateful pickers/wizards
6. **Verify through the real path:** plugin loads, command appears/runs, handler replies, buttons route; skills validate and trigger; procedures are reachable from the owning skill/project.
7. **Write state in the right home:** AID project docs for project work, skill references for runtime material, `knowledge/procedures/` for procedures, daily memory for audit. Never edit the generated SkillReef mirror directly.

## Baseline Plugin Audit Workflow

Use this when giving custom plugins the same lightweight coverage treatment as skills. Keep the audit per-plugin, scoped, and boring.

1. **Inventory from the runtime first:** use `openclaw plugins list --json` to identify current plugin roots/status, then select custom plugin roots (usually `~/.openclaw/extensions`, `~/projects/clawSean`, or workspace project plugins). Do not audit bundled `/usr/lib/node_modules/openclaw/dist/extensions/*` unless explicitly asked.
2. **One worker per plugin is fine, but cap blast radius:** each worker may edit only its plugin root. Avoid Gateway restarts, config writes, live channel sends, and live provider/API calls unless explicitly requested.
3. **Baseline coverage checklist:**
   - manifest/package sanity: `id`, `name`, `description`, activation fields, entry/runtime paths, config schema when used
   - TypeScript build path: `npm test`/`npm run build`/`npx tsc` as applicable; compiled runtime output exists when required
   - SDK compatibility: no invented command fields; imports match installed plugin SDK/types
   - offline behavior: mocked or fixture-based tests for command handlers, formatting, config validation, error paths, and callback namespace parsing
   - OpenClaw load check: `openclaw plugins inspect <id>` or `openclaw plugins doctor` when cheap and non-destructive
   - interactive plugins: verify namespaced `callback_data` + registered handler shape; real Telegram tap testing is separate and should be called out if not performed
4. **Patch only obvious gaps:** add the smallest local test/smoke script or fixture test that proves the plugin can build/load/handle its core path offline. Do not broad-refactor plugin architecture during a baseline audit.
5. **Write `BASELINE_PLUGIN_AUDIT.md` in the plugin root** with: baseline now present, commands run, pass/fail, and remaining gaps. Prefer this over burying results in chat logs.
6. **Final local verification:** after workers finish, run each detected test/build command once from the parent session and summarize pass/fail. Treat “no live API/integration test” as an explicit remaining gap, not a failure.

Pasteable worker prompt shape:

```text
You are a coding agent. Scope: exactly this OpenClaw plugin directory: <PLUGIN_DIR>.

Task: ensure this plugin has lightweight baseline functional/test coverage. Not exhaustive.

Rules: edit only <PLUGIN_DIR>; do not restart Gateway, change global config, send messages, or make live external API calls. Read package/manifest/source, add/fix the smallest useful offline test/build/load check, run the smallest verification command, and write <PLUGIN_DIR>/BASELINE_PLUGIN_AUDIT.md with coverage, commands, result, and gaps.
```

## Key Caveats

Built-in OpenClaw native commands like `/think` can use typed command definitions with `argsMenu: "auto"`. Current public plugin command types may not expose that same `argsMenu` field. Do **not** invent unsupported fields; verify `OpenClawPluginCommandDefinition` in the installed SDK. As of the inspected SDK, plugin commands expose metadata such as `name`, `nativeNames`, `nativeProgressMessages`, `description`, `agentPromptGuidance`, `acceptsArgs`, `requireAuth`, `requiredScopes`, `ownership`, and `handler`, but not core-only `args` / `choices` / `argsMenu`.

### Native progress / premessage rotation

Plugin slash commands support `nativeProgressMessages`, but in the current SDK this is command metadata, not a handler-time callback. If you want Tide Pools-style variety, define a local message array plus `pickProgress()` and set `nativeProgressMessages: { default: pickProgress() }` at `api.registerCommand(...)` time. This rotates when command metadata is rebuilt/reloaded, not guaranteed per invocation. Do not claim per-run rotation unless the installed SDK explicitly supports function/array progress values.

## Reference Files

- `references/authoring-governance.md` — house routing rules for procedure vs skill vs plugin vs AID project docs, plus known authoring pitfalls.
- `references/openclaw-plugin-manifest-build.md` — manifest activation, side-effect guarding, TypeScript/runtime output, and package build requirements.
- `references/one-shot-extension-prompt.md` — paste-ready prompt/template for generating a minimal plugin with a chat slash command.
- `references/telegram-command-buttons.md` — implementation research for `/think`-style arg menus, plugin presentation buttons, interactive handlers, and `/models`-style picker callbacks.
- `references/button-branching-feasibility.md` — preliminary feasibility verdict for two-branch plugin buttons, with source evidence and a minimal skeleton.

## Local Docs / Source to Check

Prefer local docs/source first, then live docs for verification. The global install path varies by system — check both `/usr/lib/node_modules/openclaw/` and `/usr/local/lib/node_modules/openclaw/`. In a repo clone, prefer `docs/plugins/`.

- Local docs (check whichever global path exists):
  - `{OPENCLAW_ROOT}/docs/plugins/building-plugins.md`
  - `{OPENCLAW_ROOT}/docs/plugins/sdk-entrypoints.md`
  - `{OPENCLAW_ROOT}/docs/plugins/message-presentation.md`
  - `{OPENCLAW_ROOT}/docs/tools/slash-commands.md`
- Local SDK types:
  - `{OPENCLAW_ROOT}/dist/plugin-sdk/src/plugins/types.d.ts`
  - `{OPENCLAW_ROOT}/dist/plugin-sdk/src/plugins/manifest.d.ts`
  - `{OPENCLAW_ROOT}/dist/plugin-sdk/src/auto-reply/reply-payload.d.ts`
- Live docs:
  - <https://docs.openclaw.ai/plugins/building-plugins>
  - <https://docs.openclaw.ai/plugins/sdk-entrypoints>
  - <https://docs.openclaw.ai/plugins/message-presentation>
  - <https://docs.openclaw.ai/plugins/sdk-setup>
  - <https://docs.openclaw.ai/plugins/architecture-internals>
  - <https://docs.openclaw.ai/tools/slash-commands>

Where `{OPENCLAW_ROOT}` is the first that exists of `/usr/lib/node_modules/openclaw`, `/usr/local/lib/node_modules/openclaw`, or a project-local `node_modules/openclaw`.


## WatchCatfish Pattern: Button-Steered Slash Command, No LLM

For simple Telegram plugin command steering like `/health` → Hardware/Services, use visible Telegram buttons with a tiny namespaced callback plus `api.registerInteractiveHandler(...)`. Keep the branch implementation token-free/no-LLM by having both the slash command and callback handler call the same local branch function.

1. Register one command with `acceptsArgs: true`.
2. With no args, return a small menu.
3. Return Telegram buttons with short namespaced `callback_data`, e.g. `watchcatfish:hardware`.
4. Register `api.registerInteractiveHandler({ channel: "telegram", namespace: "watchcatfish", ... })`.
5. Implement the branch as ordinary slash-arg handling (`hardware` → `core`, `services` → `services`) and call that same function from the interactive handler.
6. For non-Telegram fallback, include plain text commands: `Run /health hardware or /health services.`

Minimal Telegram menu shape from WatchCatfish:

```ts
return {
  text: [
    "🐟 WatchCatfish · Health",
    "Choose a token-free report 👇",
    "",
    "Options: 🖥️ Hardware · 🧰 Services"
  ].join("\n"),
  channelData: {
    telegram: {
      buttons: [[
        { text: "🖥️ Hardware", callback_data: "watchcatfish:hardware", style: "primary" },
        { text: "🧰 Services", callback_data: "watchcatfish:services", style: "success" }
      ]]
    }
  }
};
```

Use `presentation.buttons` when channel-agnostic rendering is verified for the target command delivery path. For Telegram-first command menus, `channelData.telegram.buttons` plus namespaced callbacks is the known-good rendering path. Avoid slash-shaped `callback_data` such as `/health services` unless you have verified the current Telegram callback dispatcher still reinjects unknown callbacks as synthetic text. Use a `/models`-style custom picker only for pagination/back/stateful menus.

### WatchCatFish Regression Lessons

- Keep the no-args button menu fast and deterministic. Do **not** replace a known-good static menu path with a long probe/dashboard path unless callbacks are separately verified; Telegram buttons should not depend on slow health checks succeeding.
- If adding probe flags, land the script and TypeScript caller together. After rollback, retest commands against current source; transient flags like `--skip-native-health` can become stale immediately.
- Verify buttons through the real channel path: command loads, menu returns visible Telegram buttons, each namespaced callback reaches `api.registerInteractiveHandler(...)`, and callback logs show no spinner/error/no-op.
- `openclaw plugins registry --refresh` rebuilds discovery metadata; it is not sufficient proof of live runtime reload.
- To reload plugin code without a full Gateway restart, trigger OpenClaw's hot config reload on a `plugins.*` path only after explicit approval for the live config mutation. Use a tiny reversible plugin config change such as `plugins.entries.<id>.config.timeoutMs` `30000 → 30001 → 30000`. Confirm logs include `config hot reload applied (...)` and `[plugin] Loaded: ...`, then restore the config value.
