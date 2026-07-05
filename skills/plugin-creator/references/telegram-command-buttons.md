# Telegram Command Buttons in OpenClaw

**Date:** 2026-05-01  
**Context:** Research seed for a future `plugin-creator` skill and interactive session tooling.

## Short Version

OpenClaw has two different button patterns that look similar in Telegram:

1. **Built-in native command arg menus** — `/think`, `/verbose`, `/trace`, etc. use command definitions with choices and `argsMenu: "auto"`. Telegram buttons rerun the command with the selected argument.
2. **Custom Telegram picker callbacks** — `/model` / `/models` uses Telegram-specific callback data (`mdl_*`) and a custom callback handler to page, go back, select, and edit the original message.

For plugin-created slash commands, verify the current SDK before assuming the built-in `argsMenu` mechanism is available. In the local SDK inspected on 2026-05-01, `OpenClawPluginCommandDefinition` exposes `acceptsArgs` and raw handler args, but not typed `args` / `argsMenu`. So plugin button branching should usually use either raw slash args or `presentation.buttons` + `api.registerInteractiveHandler(...)`.

## Live Docs / Local Sources

Live docs:

- Plugin quick start: <https://docs.openclaw.ai/plugins/building-plugins>
- Plugin entry points: <https://docs.openclaw.ai/plugins/sdk-entrypoints>
- Message presentation/buttons: <https://docs.openclaw.ai/plugins/message-presentation>
- Slash commands: <https://docs.openclaw.ai/tools/slash-commands>
- OpenClaw source root: <https://github.com/openclaw/openclaw>

Local mirrors/source inspected:

- `/usr/local/lib/node_modules/openclaw/docs/plugins/building-plugins.md`
- `/usr/local/lib/node_modules/openclaw/docs/plugins/sdk-entrypoints.md`
- `/usr/local/lib/node_modules/openclaw/docs/plugins/message-presentation.md`
- `/usr/local/lib/node_modules/openclaw/docs/tools/slash-commands.md`
- `/usr/local/lib/node_modules/openclaw/dist/plugin-sdk/src/plugins/types.d.ts`
- `/usr/local/lib/node_modules/openclaw/dist/plugin-sdk/src/auto-reply/reply-payload.d.ts`
- `/usr/local/lib/node_modules/openclaw/dist/extensions/telegram/command-ui-DaXEabc2.js`
- `/usr/local/lib/node_modules/openclaw/dist/extensions/telegram/bot-msflwCEW.js`
- `/usr/local/lib/node_modules/openclaw/dist/commands-registry.data-BMlUZTQ7.js`
- `/usr/local/lib/node_modules/openclaw/dist/commands-registry-DPcvwVIV.js`

Existing local plugin-like example:

- `projects/github/clawsean-tide-pools-plugin/index.ts`
  - registers `/tidepools` and `/quota_all` via `api.registerCommand(...)`
  - uses `acceptsArgs: true`, `requireAuth: true`, `nativeProgressMessages`, and raw args parsing
  - useful as a real-world slash-command plugin shape

## Pattern A — Built-In Native Command Arg Menus

Used by built-in commands like `/think`, `/verbose`, `/trace`, `/fast`, `/reasoning`, `/send`, and similar commands.

### Shape

The built-in command registry declares:

- `args`
- discrete `choices`, sometimes dynamic
- `argsMenu: "auto"` or an explicit `argsMenu` spec

Example identifiers from local source:

- `argsMenu: "auto"`
- `resolveCommandArgMenu(...)`
- `formatCommandArgMenuTitle(...)`
- `buildTelegramNativeCommandCallbackData(...)`
- `parseTelegramNativeCommandCallbackData(...)`
- callback prefix: `tgcmd:`

### Runtime Behavior

The button callback is not a bespoke workflow. It becomes an equivalent command invocation.

Example conceptual flow:

1. User sends `/think`.
2. OpenClaw resolves thinking levels for the current session model.
3. Telegram sends a button menu.
4. User taps `medium`.
5. Callback data maps to a synthetic native command, conceptually `/think medium`.
6. Normal command handling applies the setting.

### Why This Is Nice

It is the cleanest UX for one-step choices because command logic stays ordinary: no state machine, no custom callback parser, no message-edit flow.

### Plugin Caveat

This pattern is available to OpenClaw's built-in command definitions. As of the local SDK inspected here, public plugin commands do **not** expose the same typed `args` + `argsMenu` fields:

- `OpenClawPluginCommandDefinition`
- `api.registerCommand(...)`
- fields observed: `name`, `nativeNames`, `nativeProgressMessages`, `description`, `agentPromptGuidance`, `acceptsArgs`, `requireAuth`, `handler`

So for plugin commands, do not write docs or prompts that blindly tell agents to use `argsMenu` unless the current SDK types show support.

## Pattern B — Custom Telegram Picker Callbacks

Used by `/model` / `/models` picker behavior.

### Shape

The model picker uses Telegram-specific callback payloads and dedicated handler logic.

Observed callback shapes:

- `mdl_prov` — show provider list
- `mdl_list_{provider}_{page}` — list models for provider/page
- `mdl_sel_{provider}/{model}` — select model
- `mdl_sel/{model}` — compact fallback when callback data would be too long
- `mdl_back` — return to provider list

### Runtime Behavior

The Telegram callback handler recognizes model-picker callbacks before falling back to generic command handling.

Conceptual flow:

1. User opens `/models` picker.
2. Telegram sends provider/model buttons.
3. User taps provider/page/model/back.
4. Handler parses callback data via `parseModelCallbackData(...)`.
5. Handler authorizes sender.
6. Handler loads current session/model state.
7. Handler edits the existing Telegram message with the next menu or result.
8. On selection, handler updates session store and clears/replaces buttons.

Relevant identifiers:

- `parseModelCallbackData(...)`
- `buildTelegramModelsMenuButtons(...)`
- `buildModelsKeyboard(...)`
- `resolveModelSelection(...)`
- callback prefix family: `mdl_*`

### Best Use

Use this only for a real interactive UI:

- pagination
- back/forward buttons
- edit-in-place menus
- compact callback encoding
- stateful selection
- special authorization behavior

For a two-branch plugin command, this is usually overkill.

## Pattern C — Plugin Presentation Buttons + Interactive Handler

This is the likely plugin-owned route for button branching today.

Message presentation is the channel-agnostic contract for rich UI. It supports button blocks whose `value` can route back through the channel's interaction path when supported.

Relevant docs/source:

- live: <https://docs.openclaw.ai/plugins/message-presentation>
- local: `/usr/local/lib/node_modules/openclaw/docs/plugins/message-presentation.md`
- type import noted in docs: `openclaw/plugin-sdk/interactive-runtime`
- reply payload type includes `presentation?: MessagePresentation`
- plugin API type includes `registerInteractiveHandler(...)`

Conceptual command result:

```ts
return {
  text: "Choose a branch:",
  presentation: {
    title: "Example",
    tone: "info",
    blocks: [
      { type: "text", text: "Choose a branch:" },
      {
        type: "buttons",
        buttons: [
          { label: "🧭 Plan", value: "example:plan", style: "primary" },
          { label: "🛠️ Run", value: "example:run", style: "success" }
        ]
      }
    ]
  }
};
```

Conceptual interactive registration:

```ts
api.registerInteractiveHandler({
  channel: "telegram",
  namespace: "example",
  async handler(ctx) {
    // Callback data matching uses namespace before `:`.
    // Payload after `example:` is the branch, e.g. `plan` or `run`.
    // Telegram ctx.respond is an object, not a function. Prefer editMessage/clearButtons for button callbacks.
    if (ctx.callback?.payload === "plan") {
      await ctx.respond.editMessage({ text: "Planning..." });
      return { handled: true };
    }
    await ctx.respond.clearButtons();
    return { handled: true };
  }
});
```

Verify exact context shape before shipping. The local dispatch path splits callback data by namespace and payload, then invokes the registered handler.

## Decision Rule

- Built-in command, one argument choice → **native command arg menu** (`argsMenu: "auto"`).
- Plugin command, one argument choice, no plugin `argsMenu` support → **raw slash args** or **presentation buttons + interactive handler**.
- Multi-step wizard, pagination, back buttons, edit-in-place → **custom interactive handler**.
- Agent conversational prompt outside plugin command → **normal Telegram button send path**.

## Two-Branch Plugin Button Recipe

For “tap A or B, then run the right branch” in a plugin:

1. Register the slash command with `api.registerCommand(...)`.
2. If current SDK supports plugin typed args + `argsMenu`, use that: it is the `/think` pattern and the tap reruns the command with the selected arg.
3. If plugin `argsMenu` is not exposed, return a `ReplyPayload` with `presentation.blocks[{ type: "buttons" }]`.
4. Use short namespaced values: `myPlugin:branchA`, `myPlugin:branchB` (64-byte Telegram callback-data limit).
5. Register `api.registerInteractiveHandler({ channel: "telegram", namespace: "myPlugin", handler })`.
6. In the handler, parse the payload after the namespace and call the same branch functions the slash command uses. For Telegram, use `ctx.respond.editMessage(...)`, `ctx.respond.clearButtons()`, `ctx.respond.reply(...)`, `ctx.respond.editButtons(...)`, or `ctx.respond.deleteMessage()`; do not call `ctx.respond(...)`.
7. Keep `/models`-style custom callback menus only for advanced UX: paging, back buttons, edit-in-place, or persistent state.

Practical rule: **try `/think` style if the SDK exposes it; otherwise use presentation buttons + interactive handler. Do not build a `/models` clone for two buttons.**

## Implementation Notes for Future `plugin-creator` Skill

- Start with a boring working slash command before adding buttons.
- In one-shot prompts, explicitly tell the coding agent to inspect the installed SDK types before using `argsMenu`.
- Prefer channel-agnostic `presentation.buttons`; avoid Telegram-only payloads until a Telegram-specific flow is truly required.
- Namespace callback values: `pluginId:action`.
- Keep callback values short; Telegram callback data is limited to 64 bytes.
- For group chats, consider original-sender checks when actions are sensitive.

## Related Project Links

- `projects/plugin-creator/research/one-shot-extension-prompt.md`
- `projects/interactive-sessions/README.md`
- `skills/telegram-ui/SKILL.md`
- `projects/interactive-sessions/research/slack-interactivity.md`


## Pattern D — Telegram `channelData` Buttons That Reinvoke Plugin Slash Args

WatchCatfish originally used a simpler no-LLM branch pattern for plugin commands where a Telegram button maps directly to an ordinary slash command invocation. Instead of maintaining callback state, the menu returns Telegram-specific `channelData.telegram.buttons` and each button's `callback_data` is the exact command branch:

```ts
{ text: "🖥️ Hardware", callback_data: "/health hardware", style: "primary" }
{ text: "🧰 Services", callback_data: "/health services", style: "success" }
```

This depended on Telegram callback dispatch presenting unknown callback data as synthetic text, so the command path received `/health hardware` or `/health services` and the normal plugin `ctx.args` branch logic ran. Treat this as a compatibility shortcut, not the canonical plugin button pattern: it is more sensitive to dispatcher, auth, and callback-routing changes than a namespaced plugin interactive handler.

Use this pattern when all of these are true:

- the button's meaning is equivalent to a slash command plus args;
- branch names are short and safe to show as commands;
- no pagination/back/edit-in-place state is needed;
- non-Telegram users can use the same explicit text commands.
- the current OpenClaw Telegram callback dispatcher has been verified to reinject unknown slash-shaped callback data as synthetic command text.

Prefer an explicit namespaced callback plus `api.registerInteractiveHandler(...)` for new plugins. For Telegram-first command menus, `channelData.telegram.buttons` with short namespaced `callback_data` values like `watchcatfish:hardware` is a known-good visible button path; register a matching namespace and have the handler call the same branch function used by `/health hardware`. Use `presentation.buttons` when channel-agnostic rendering is verified for the target delivery path. Do **not** use raw slash-shaped callbacks for opaque callback payloads, destructive actions needing confirmation state, or flows where buttons should edit the original message.

WatchCatfish also added aliases so human text and callback values converge:

- `/health hardware` → `core` probe
- `/health basic` → `core` probe
- `/health services` → services probe

This remains a useful fallback pattern, but the most reproducible pattern for “buttons steer a plugin while the plugin owns the whole no-LLM execution path” is now visible buttons with namespaced callback data plus an explicit interactive handler.
