# One-Shot Prompt — Create an OpenClaw Slash-Command Plugin

**Goal:** Give a coding agent enough verified context to create a minimal OpenClaw extension/plugin that works from chat as a slash command.

Use this as a prompt template. Fill the bracketed fields and paste it into a coding agent with access to the target repo/workspace.

---

## Paste-Ready Prompt

```text
Create a minimal OpenClaw plugin/extension named [PLUGIN_ID] that registers a chat slash command /[COMMAND_NAME].

User-facing behavior:
- /[COMMAND_NAME] [ARGS] should [DESCRIBE ACTION].
- Return a concise text reply on success.
- Return a helpful error reply on failure.
- Do not require external network calls unless explicitly needed.

Target location:
- Create or update package at [TARGET_DIR].

Implementation requirements:
1. Create a plugin manifest `openclaw.plugin.json` with:
   - id: [PLUGIN_ID]
   - name: [HUMAN_NAME]
   - description: [ONE_SENTENCE_DESCRIPTION]
   - activation.onStartup: false (unless the plugin must import during gateway startup)
   - empty config schema unless config is truly needed.
2. Create/update `package.json` with:
   - `type: "module"`
   - `openclaw.extensions` pointing to the source entry, usually `./index.ts` or `./src/index.ts`
   - `openclaw.runtimeExtensions` pointing to the compiled JS peer (e.g. `./dist/index.js`). This is required for all installed plugins — local, npm, and ClawHub. Without it, OpenClaw warns about missing compiled runtime output even for local installs.
   - `scripts.build` set to `"tsc"` for easy recompilation
   - compatible OpenClaw/plugin SDK version fields if this package is meant for publishing.
3. Create `tsconfig.json` for TypeScript compilation:
   ```json
   {
     "compilerOptions": {
       "target": "ES2022",
       "module": "Node16",
       "moduleResolution": "Node16",
       "outDir": "./dist",
       "rootDir": "./src",
       "declaration": true,
       "esModuleInterop": true,
       "skipLibCheck": true,
       "allowJs": true,
       "strict": false
     },
     "include": ["src"]
   }
   ```
   Adjust `rootDir` if the entry is at `./index.ts` instead of `./src/index.ts`.
4. Compile TypeScript to JavaScript:
   ```bash
   npx tsc
   ```
   This produces `dist/index.js` which `runtimeExtensions` points to. The compiled output must exist before the plugin can load without warnings.
5. Create the entry point using the current OpenClaw plugin SDK:
   - Prefer `definePluginEntry` from `openclaw/plugin-sdk/plugin-entry` when available.
   - Register the command with `api.registerCommand({ name, description, acceptsArgs, requireAuth, nativeProgressMessages, handler })`.
   - The command name must not include the leading slash.
   - Guard side effects (DB connections, background workers, network clients) behind `api.registrationMode === "full"`. OpenClaw calls register() during discovery scans too.
6. In the command handler:
   - Read raw args from the current plugin command context shape.
   - Validate args.
   - Return a `ReplyPayload` object, usually `{ text: "..." }`.
7. If the command needs a simple branch choice:
   - First check current SDK types for plugin command typed args / `argsMenu` support.
   - If plugin `argsMenu` is not exposed, do NOT invent it.
   - Instead use either:
     a. raw slash args such as `/[COMMAND_NAME] plan`, `/[COMMAND_NAME] run`; or
     b. return `presentation.blocks` with `buttons`, and register an interactive handler with `api.registerInteractiveHandler(...)` if supported.
8. If adding interactive buttons:
   - Use channel-agnostic `presentation.buttons` where possible.
   - Button values must be short and namespaced, e.g. `[PLUGIN_ID]:plan`.
   - Register an interactive handler namespace matching the prefix if the channel routes button values to plugin handlers.
   - Keep Telegram callback payloads short (Telegram callback data is 64 bytes max); store larger state under a short id if needed.
   - Telegram interactive `ctx.respond` is an object, not a function. Use methods such as `ctx.respond.editMessage(...)`, `ctx.respond.reply(...)`, `ctx.respond.clearButtons()`, `ctx.respond.editButtons(...)`, or `ctx.respond.deleteMessage()`.
9. Add a README with install/test/use instructions.
10. Add the smallest useful verification command/check for this repo.

Research/verification sources to inspect before coding (check /usr/lib or /usr/local/lib, whichever exists):
- Local docs:
  - `{OPENCLAW_ROOT}/docs/plugins/building-plugins.md`
  - `{OPENCLAW_ROOT}/docs/plugins/sdk-entrypoints.md`
  - `{OPENCLAW_ROOT}/docs/plugins/message-presentation.md`
  - `{OPENCLAW_ROOT}/docs/tools/slash-commands.md`
  - `{OPENCLAW_ROOT}/docs/snippets/plugin-publish/minimal-package.json`
- Local SDK/source types:
  - `{OPENCLAW_ROOT}/dist/plugin-sdk/src/plugins/types.d.ts`
  - `{OPENCLAW_ROOT}/dist/plugin-sdk/src/plugins/manifest.d.ts`
  - `{OPENCLAW_ROOT}/dist/plugin-sdk/src/auto-reply/reply-payload.d.ts`
- Live docs:
  - https://docs.openclaw.ai/plugins/building-plugins
  - https://docs.openclaw.ai/plugins/sdk-entrypoints
  - https://docs.openclaw.ai/plugins/message-presentation
  - https://docs.openclaw.ai/tools/slash-commands
- Source root for drift checks:
  - https://github.com/openclaw/openclaw

Existing local example to compare, if present:
- `projects/github/clawsean-tide-pools-plugin/index.ts`
  - registers `/tidepools` and `/quota_all` with `api.registerCommand(...)`
  - useful as a real plugin command shape, though it uses raw args rather than typed arg menus.

Important current caveat:
- Built-in OpenClaw native commands like `/think` use typed command definitions with `argsMenu: "auto"` to render Telegram buttons.
- The public plugin command definition in current local SDK may only expose `name`, `nativeNames`, `nativeProgressMessages`, `description`, `agentPromptGuidance`, `acceptsArgs`, `requireAuth`, and `handler`.
- Therefore, do not assume plugin commands can use `argsMenu` unless the current SDK types explicitly show it.

Deliverables:
- `openclaw.plugin.json`
- `package.json` (with `openclaw.runtimeExtensions` and `build` script)
- `tsconfig.json`
- plugin entry file (TypeScript source)
- `dist/index.js` (compiled output — run `npx tsc` before testing)
- README usage section showing `/[COMMAND_NAME]`
- optional interactive handler only if verified against current SDK types
- verification output summary
```

---

## Minimal Command Skeleton

This is a shape reference, not a guarantee against SDK drift. Verify against `types.d.ts` in the installed OpenClaw version.

```ts
import { definePluginEntry } from "openclaw/plugin-sdk/plugin-entry";

export default definePluginEntry({
  id: "example-plugin",
  name: "Example Plugin",
  description: "Registers /example for chat use.",
  register(api) {
    api.registerCommand({
      name: "example",
      description: "Run the example command.",
      acceptsArgs: true,
      requireAuth: true,
      // Progress text is command metadata. For Tide Pools-style variety, define
      // an array + pickProgress() and call it here at registration time; this
      // rotates on metadata rebuild/reload, not guaranteed per invocation.
      nativeProgressMessages: { default: "Running example..." },
      async handler(ctx) {
        const raw = String(ctx?.args ?? "").trim();
        if (raw === "plan") return { text: "Plan branch selected." };
        if (raw === "run") return { text: "Run branch selected." };
        return { text: "Usage: /example plan or /example run" };
      },
    });
  },
});
```

## Button Branch Skeleton

Use this only after verifying `ReplyPayload.presentation` and `api.registerInteractiveHandler(...)` behavior in the current SDK/channel.

```ts
api.registerCommand({
  name: "example",
  description: "Run the example command.",
  requireAuth: true,
  async handler() {
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
              { label: "🛠️ Run", value: "example:run", style: "success" },
            ],
          },
        ],
      },
    };
  },
});

api.registerInteractiveHandler({
  channel: "telegram",
  namespace: "example",
  async handler(ctx) {
    // Current dispatch splits callback data as namespace + payload after `:`.
    // Verify exact ctx shape against the installed SDK before shipping.
    if (ctx.callback?.payload === "plan") {
      await ctx.respond.editMessage({ text: "Plan branch selected." });
      return { handled: true };
    }
    if (ctx.callback?.payload === "run") {
      await ctx.respond.editMessage({ text: "Run branch selected." });
      return { handled: true };
    }
    await ctx.respond.clearButtons();
    return { handled: true };
  },
});
```

## Verification Checklist

- `openclaw.plugin.json` exists, id matches the entry id, and `activation.onStartup` is set.
- `package.json` declares `openclaw.extensions` (source) and `openclaw.runtimeExtensions` (compiled JS).
- `tsconfig.json` exists with `outDir: "./dist"` matching `runtimeExtensions`.
- `npx tsc` compiles without errors and `dist/index.js` exists.
- `api.registerCommand(...)` is called exactly once per slash command.
- Command name has no leading slash.
- If using `nativeProgressMessages`, remember values are static metadata strings in the current SDK; `pickProgress()` at registration can vary across reloads but is not per-run guaranteed.
- Handler returns `{ text: string }` or another valid `ReplyPayload`.
- `openclaw` can load/discover the plugin without startup errors.
- `/help` or `/commands` shows the command if native command metadata is exposed.
- Sending `/[COMMAND_NAME]` from Telegram/Slack reaches the handler.
- If buttons are used, tapping each button triggers the intended branch; stale/unauthorized taps are handled safely; and the original button message is edited or cleared so stale buttons do not linger.

## When to Use Which Button Pattern

- Simple branch and plugin SDK supports typed arg menus → use command choices/arg menu.
- Simple branch and plugin SDK does **not** support typed arg menus → use raw slash args or presentation buttons + interactive handler.
- Multi-step picker, pagination, back buttons, edit-in-place → custom interactive handler.

## Related References

- `projects/plugin-creator/research/telegram-command-buttons.md`
- `projects/plugin-creator/README.md`
- `projects/interactive-sessions/README.md`
