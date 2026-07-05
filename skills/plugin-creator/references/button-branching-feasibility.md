# Plugin Button Branching Feasibility — Preliminary Research

**Date:** 2026-05-01  
**Question:** Can an OpenClaw plugin expose a chat slash command that offers two buttons and branches based on the button tapped?

## Short Answer

**Yes, feasible today** using `presentation.buttons` plus `api.registerInteractiveHandler(...)`.

**Not feasible today via `/think`-style `argsMenu: "auto"` for public plugin commands**, unless the plugin SDK grows typed command args. The built-in command system supports `argsMenu`; the public plugin command API currently does not expose it.

## Recommended Implementation Path

For a two-choice plugin command:

1. Register a normal plugin slash command with `api.registerCommand(...)`.
2. When no/ambiguous args are supplied, return a `ReplyPayload` with `presentation.blocks` containing a `buttons` block.
3. Give each button a namespaced value such as:
   - `myPlugin:branchA`
   - `myPlugin:branchB`
4. Register a Telegram interactive handler:
   - `api.registerInteractiveHandler({ channel: "telegram", namespace: "myPlugin", handler })`
5. In the handler, branch on `ctx.callback.payload` (`branchA` / `branchB`) and call the same functions used by `/mycommand branchA` and `/mycommand branchB`.

This gives us the UX we want without building a `/models`-style custom picker.

## Evidence: Plugin Command API

Local installed SDK type:

- `/usr/local/lib/node_modules/openclaw/dist/plugin-sdk/src/plugins/types.d.ts`

`OpenClawPluginCommandDefinition` exposes:

```ts
export type OpenClawPluginCommandDefinition = {
  name: string;
  nativeNames?: Partial<Record<string, string>> & { default?: string };
  nativeProgressMessages?: Partial<Record<string, string>> & { default?: string };
  description: string;
  agentPromptGuidance?: readonly string[];
  acceptsArgs?: boolean;
  requireAuth?: boolean;
  requiredScopes?: OperatorScope[];
  ownership?: "plugin" | "reserved";
  handler: PluginCommandHandler;
};
```

No `args`, `choices`, or `argsMenu` field is exposed here.

Command matching/execution source:

- `/usr/local/lib/node_modules/openclaw/dist/commands-CgVoTNyj.js`

Findings:

- Plugin slash commands are matched before built-ins.
- `acceptsArgs: false` makes `/cmd arg` fall through instead of matching.
- Args are passed as a single sanitized string: `ctx.args`.
- Handler returns `ReplyPayload`.

Implication: plugin authors can implement `/cmd branchA`, but cannot currently ask the native command system to auto-render typed arg choices from plugin metadata.

## Evidence: Presentation Buttons Render on Telegram

Local Telegram outbound renderer:

- `/usr/local/lib/node_modules/openclaw/dist/extensions/telegram/channel-YQC5fGmM.js`

Findings:

- Telegram declares `presentationCapabilities.supported = true` and `buttons = true`.
- `renderPresentation(...)` converts `presentation` into `interactive` via `presentationToInteractiveReply(...)`.
- `sendTelegramPayloadMessages(...)` resolves inline buttons from `payload.interactive`.

Button rendering source:

- `/usr/local/lib/node_modules/openclaw/dist/extensions/telegram/button-types-LgfH7iW7.js`
- `/usr/local/lib/node_modules/openclaw/dist/extensions/telegram/send-PMS8bE6c.js`

Findings:

- Button `value` becomes Telegram `callback_data` after sanitization.
- Buttons are chunked into rows of 3.
- Telegram inline keyboard is built from `{ text, callback_data }`.

Live docs corroboration:

- <https://docs.openclaw.ai/plugins/message-presentation>

Docs state that `MessagePresentationButton.value` is routed back through the channel interaction path when supported.

## Evidence: Plugin Interactive Handler Dispatch Exists

Local SDK/runtime files:

- `/usr/local/lib/node_modules/openclaw/dist/plugin-sdk/src/plugins/interactive.d.ts`
- `/usr/local/lib/node_modules/openclaw/dist/plugin-sdk/src/plugins/interactive-registry.d.ts`
- `/usr/local/lib/node_modules/openclaw/dist/types-CSFx9bdF.js`
- `/usr/local/lib/node_modules/openclaw/dist/extensions/telegram/bot-msflwCEW.js`

Findings:

- `registerInteractiveHandler` is exposed on the plugin API.
- Interactive handlers are registered by `(channel, namespace)`.
- Callback data is parsed as:
  - namespace = text before the first `:`
  - payload = text after the first `:`
- Namespace validation allows letters, numbers, dots, underscores, and hyphens.
- Telegram callback handler calls `dispatchTelegramPluginInteractiveHandler(...)` before later built-in approval/model callback handling.
- Telegram passes handler context including:
  - `channel: "telegram"`
  - `callback.data`
  - `callback.namespace`
  - `callback.payload`
  - `callback.messageId`
  - `callback.chatId`
  - `callback.messageText`
  - `respond.reply(...)`
  - `respond.editMessage(...)`
  - `respond.editButtons(...)`
  - `respond.clearButtons(...)`
  - `respond.deleteMessage(...)`

Important: `respond` is an object with methods, not a callable function. Do not write `await ctx.respond({ text: "..." })`.

Implication: namespaced button values like `example:branchA` should route cleanly to a plugin handler registered with namespace `example`.

## Pattern Comparison

### Pattern A — `/think`-style native arg menu

Good for built-in commands. The command definition declares typed args, choices, and `argsMenu: "auto"`. Telegram creates buttons that rerun the same command with the selected arg.

Current plugin feasibility: **not available through public plugin command type**.

### Pattern B — `/models`-style custom Telegram picker

Good for multi-page/stateful menus where the same Telegram message is edited repeatedly.

Current plugin feasibility: **possible in spirit via interactive handlers**, but overkill for two branches.

### Pattern C — Plugin presentation buttons + interactive handler

Good for simple plugin-owned branches.

Current plugin feasibility: **yes, recommended**.

## Minimal Shape

```ts
api.registerCommand({
  name: "example",
  description: "Choose one of two branches",
  acceptsArgs: true,
  async handler(ctx) {
    const arg = ctx.args?.trim().toLowerCase();
    if (arg === "a") return runBranchA(ctx);
    if (arg === "b") return runBranchB(ctx);

    return {
      text: "Choose a branch:",
      presentation: {
        blocks: [
          { type: "text", text: "Choose a branch:" },
          {
            type: "buttons",
            buttons: [
              { label: "Branch A", value: "example:a", style: "primary" },
              { label: "Branch B", value: "example:b", style: "secondary" }
            ]
          }
        ]
      }
    };
  }
});

api.registerInteractiveHandler({
  channel: "telegram",
  namespace: "example",
  async handler(ctx: any) {
    if (ctx.callback?.payload === "a") {
      await ctx.respond.editMessage({ text: "Running branch A..." });
      const result = await runBranchA(ctx);
      await ctx.respond.reply({ text: result.text ?? "Branch A done." });
      return { handled: true };
    }

    if (ctx.callback?.payload === "b") {
      await ctx.respond.editMessage({ text: "Running branch B..." });
      const result = await runBranchB(ctx);
      await ctx.respond.reply({ text: result.text ?? "Branch B done." });
      return { handled: true };
    }

    await ctx.respond.clearButtons();
    await ctx.respond.reply({ text: "Unknown choice." });
    return { handled: true };
  }
});
```

## Open Questions / Risks

1. **Handler context typing is weak.** `PluginInteractiveHandlerRegistration` defaults context to `unknown`; examples may need a local `TelegramInteractiveContext` type or `ctx: any` until OpenClaw exports stronger types.
2. **Cross-channel behavior needs per-channel handlers.** Telegram is clearly wired. Slack/Discord also dispatch plugin interactive handlers, but button rendering/callback shape should be separately verified before promising parity.
3. **Button value length/sanitization.** Telegram callback data is constrained by Telegram to 64 bytes. Keep values short and namespaced. Use server-side state keyed by a compact id for larger state.
4. **Auth behavior.** Telegram callback dispatch occurs after sender authorization checks, and handler context includes `auth: { isAuthorizedSender: true }` for authorized callbacks. Still validate sensitive branch actions inside the plugin.
5. **Handled semantics.** Return `{ handled: true }` when the callback is consumed. Return `{ handled: false }` only when intentionally allowing later channel callback handling to continue.
5. **Native command menus for plugins would be nicer.** A future SDK enhancement could add typed plugin command args + `argsMenu`, making two-branch slash commands as clean as `/think`.

## Feasibility Verdict

**Green for Telegram two-button branching using presentation buttons + plugin interactive handler.**

Do a tiny proof-of-concept next: one plugin command `/branchdemo`, two buttons, one handler, verify:

- `/branchdemo` sends inline Telegram buttons.
- Tapping Branch A/B reaches the plugin handler.
- Handler can edit/clear buttons and post the branch result.

If that works, fold the resulting working plugin skeleton into `plugin-creator` as the canonical one-shot example.


## Addendum: Even Simpler Pattern for Slash-Equivalent Branches

After the first feasibility note, WatchCatfish tried a lower-overhead branch style for `/health`: return Telegram `channelData.telegram.buttons` whose `callback_data` values are literal command invocations such as `/health hardware` and `/health services`. That shortcut depends on Telegram routing unknown callbacks back as synthetic text, so it can regress when callback dispatch, auth gating, or command reinjection changes.

Recommendation update:

- Use visible buttons with namespaced callback data plus `api.registerInteractiveHandler(...)` first for plugin-owned buttons, even when the branch can be represented as `/command arg`.
- For Telegram-first command menus, `channelData.telegram.buttons` is the known-good visible rendering path; use `presentation.buttons` when channel-agnostic rendering is verified for the target delivery path.
- Keep the callback value short and namespaced (`example:a`), and have the handler call the same branch function used by slash args.
- Use raw `channelData.telegram.buttons` with slash-shaped `callback_data` only as a compatibility fallback after verifying the live Telegram callback path.
- If the UX needs pages/back/select/edit-in-place, use a custom interactive handler/picker.

This keeps two-branch no-LLM command plugins easy to reproduce without relying on implicit synthetic command reinjection.
