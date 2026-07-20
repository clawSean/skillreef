# Payload Recipes — message tool JSON for every Telegram action

Copy-paste payloads for the rules in SKILL.md's Action Rules section. `target` defaults to the current source conversation — include it only when sending elsewhere. Omit `channel` unless sending outside the current channel. Message bodies below are plain markdown/text (house default since 2026-07-20); use explicit rich-body HTML only as the stale-client fallback per SKILL.md.

## Mentions

```json
{ "action": "send", "target": "telegram:<group_chat_id>",
  "message": "<a href=\"tg://user?id=<user_id>\">Nick</a> this one is yours." }
```

- `tg://user?id=<id>` works because raw `<a href>` is whitelisted by the renderer.
- Keep display names simple inside the `<a>` tag — no raw `<`, `>`, `&`.
- IDs from trusted runtime metadata or contact/group memory are safe; uncertain identity → say so or use plain name.

## Buttons (canonical: presentation.blocks)

```json
{ "action": "send", "target": "<chat_id>",
  "message": "Question text 👇",
  "presentation": { "blocks": [
    { "type": "buttons", "buttons": [
      { "label": "✅ Yes", "value": "yes", "style": "success" },
      { "label": "❌ No", "value": "no", "style": "danger" }
    ]}
  ]}}
```

Three button kinds — `value` (callback), `url` (link), `webApp.url` (WebApp; legacy `web_app` accepted). Mixing URL + callback in one keyboard is verified live (2026-07-04). Styles: `primary`, `secondary`, `success`, `danger`.

**Verification history:** raw top-level `buttons` param verified silently dropped live 2026-07-06 (Clawloop msg 18942 — `ok: true`, no keyboard; MCP schema strips it). Presentation-only send fails `Message must be non-empty` (2026-07-06). URL buttons + mixed keyboards live-verified 2026-07-04 (earlier "broken in renderer" claims stale — `toInlineKeyboardButton` handles all three kinds). WebApp button in DM verified 2026-07-04 (rendered, opened in-app webview).

### Group Mini App launch (live-verified 2026-07-09, Claw Four in Dev Team)

Mini Apps launch fine from groups — the proven group path is a normal URL button to the BotFather Mini App direct link (opens natively as the Mini App; the keyboard always renders). Only the true `webApp` button KIND gets dropped by Telegram in unproven group keyboards (correction recorded 2026-07-09 08:16 UTC: the working Dev Team button was a URL button, not a true `webApp` button):

```json
{ "action": "send",
  "message": "Claw Four is live 🦞🎮 Tap in and choose your name.",
  "presentation": { "blocks": [
    { "type": "buttons", "buttons": [
      { "label": "🎮 Play", "url": "https://t.me/<bot_username>/<app_short_name>?startapp=<room_or_payload>", "style": "success" },
      { "label": "🌐 Browser", "url": "https://example.com/?room=<room>", "style": "secondary" }
    ]}
  ]}}
```

Launch hierarchy: group/topic → Mini App direct-link URL button first, browser fallback second, naked link last. Private chat → true `webApp` button preferred. Unknown surface → direct-link URL button + browser fallback; only add true `webApp` after proving the chat renders it.

### Grid layouts (row structure)

- Binary: one row — `✅ Yes · ❌ No`
- Binary + defer: two rows — `✅ Do it · ❌ Cancel` / `⏰ Not now`
- Three+ choices: one per row, stacked

### Button emoji intents

✅ yes/approve · ❌ no/cancel · ⏰ later/defer · ⚠️ danger/destructive · ℹ️ info · 🔒 lock in · 🅰️🅱️ neutral A/B

## Selects

```json
{ "type": "select", "placeholder": "Choose lane",
  "options": [
    { "label": "🔐 Security", "value": "security" },
    { "label": "🦞 Product", "value": "product" }
  ]}
```

Renders as buttons on Telegram; real dropdown on Slack.

## Polls

```json
{ "action": "poll", "target": "<chat_id>",
  "pollQuestion": "Which approach?",
  "pollOption": ["Option A", "Option B", "Option C"],
  "pollAnonymous": false,
  "pollDurationSeconds": 300 }
```

Flags: `pollAnonymous`/`pollPublic` (voter visibility), `pollMulti` (multi-select), `pollDurationSeconds` (auto-close, 5–600).

## Edits

```json
{ "action": "edit", "target": "<chat_id>", "messageId": "<message_id>", "message": "Updated text here." }
```

## Replies

```json
{ "action": "send", "target": "<chat_id>", "message": "Replying to that ^", "replyTo": "<message_id>" }
```

## Reactions

```json
{ "action": "react", "target": "<chat_id>", "messageId": "<message_id>", "emoji": "👍" }
```

Remove with `"remove": true`. (🦞 in the default set: tested & failed 2026-02-13.)

## Media / Files

```json
{ "action": "send", "target": "<chat_id>", "media": "/absolute/path/to/file.png",
  "message": "Caption text", "forceDocument": true }
```

Caption formatting (bold/strike/spoiler/links) verified live 2026-06-10.

## Stickers

```json
{ "action": "sticker", "target": "<chat_id>", "stickerId": ["<fileId>"] }
```

```json
{ "action": "sticker-search", "query": "cat waving", "limit": 5 }
```

## Pins

```json
{ "action": "send", "target": "<chat_id>", "message": "Pinned announcement", "delivery": { "pin": true } }
```

CLI: `--pin`.

## Presentation card block support (Telegram)

- ✅ `text` → message body · ✅ `context` → body (no visual distinction) · ✅ `buttons`/`select` → inline keyboard
- ⚠️ `divider` → not rendered · `tone` → no visual effect (matters on Slack/Teams) · `title` → prepended to body

## Plugin Reply Buttons (`channelData.telegram.buttons`)

Plugin-owned command menus only (no-LLM slash-command steering where the callback re-enters the command path). Ordinary assistant sends use `presentation.blocks`.

```ts
return {
  text: "Choose a report 👇\n\nOptions: 🖥️ Hardware · 🧰 Services",
  channelData: {
    telegram: {
      buttons: [[
        { text: "🖥️ Hardware", callback_data: "/health hardware" },
        { text: "🧰 Services", callback_data: "/health services" }
      ]]
    }
  }
};
```

Mirror the options in message text either way.
