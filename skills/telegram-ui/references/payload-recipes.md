# Telegram Payload Recipes

Use these only after `SKILL.md` selects the explicit `message` path. `target`
defaults to the current source conversation; include it only for another chat.
All button examples use current typed actions. Legacy `value`, `url`, `webApp`,
and `web_app` aliases are compatibility inputs, not authoring defaults.

## Mention

```json
{ "action": "send", "target": "telegram:<group_chat_id>", "message": "<a href=\"tg://user?id=<user_id>\">Nick</a> this one is yours." }
```

Prefer `replyTo`, then a trusted `tg://user?id=` mention, then `@username`, then
plain name. Never invent an ID.

## Callback buttons

```json
{
  "action": "send",
  "message": "Choose one 👇",
  "presentation": { "blocks": [{
    "type": "buttons",
    "buttons": [
      { "label": "✅ Yes", "action": { "type": "callback", "value": "yes" }, "style": "success" },
      { "label": "❌ No", "action": { "type": "callback", "value": "no" }, "style": "danger" }
    ]
  }] }
}
```

Use stable lowercase snake_case callback values. Mirror options in the message.
Top-level `buttons` are stripped; `presentation` does not replace `message`.
Telegram auto-chunks three buttons per row, so keep 3+ button labels short.

## Copy Text — future payload shape

The availability, limit, and fallback rule is owned by
[SKILL.md](../SKILL.md#copyability). This shape is intentionally non-executable
until that capability gate passes.

```json
{
  "action": "send",
  "message": "Token: `TOKEN-7319`",
  "presentation": { "blocks": [{
    "type": "buttons",
    "buttons": [{ "label": "📋 Copy token", "action": { "type": "copy-text", "text": "TOKEN-7319" } }]
  }] }
}
```

## URL button

```json
{
  "action": "send",
  "message": "Open the report 👇",
  "presentation": { "blocks": [{
    "type": "buttons",
    "buttons": [{ "label": "📄 Report", "action": { "type": "url", "url": "https://example.com/report" } }]
  }] }
}
```

## Mini App

Surface selection is owned by [SKILL.md](../SKILL.md#4-choose-the-interaction).
Group/topic direct-link shape:

```json
{
  "action": "send",
  "message": "The Mini App is ready 🦞🎮",
  "presentation": { "blocks": [{
    "type": "buttons",
    "buttons": [
      { "label": "🎮 Play", "action": { "type": "url", "url": "https://t.me/<bot_username>/<app_short_name>?startapp=<payload>" }, "style": "success" },
      { "label": "🌐 Browser", "action": { "type": "url", "url": "https://example.com/?room=<room>" }, "style": "secondary" }
    ]
  }] }
}
```

Private-chat shape after the canonical surface gate passes:

```json
{
  "label": "🎮 Open app",
  "action": { "type": "web-app", "url": "https://example.com/app" }
}
```

## Select

```json
{
  "type": "select",
  "placeholder": "Choose lane",
  "options": [
    { "label": "🔐 Security", "action": { "type": "callback", "value": "security" } },
    { "label": "🦞 Product", "action": { "type": "callback", "value": "product" } }
  ]
}
```

Telegram renders selects as buttons; use a select only when a shared flow also
targets a channel with a real dropdown.

## Poll

```json
{ "action": "poll", "pollQuestion": "Which approach?", "pollOption": ["Option A", "Option B", "Option C"], "pollAnonymous": false, "pollDurationSeconds": 300 }
```

Use `pollMulti` for multi-select. Auto-close accepts 5–604800 seconds.

## Edit

```json
{ "action": "edit", "target": "<numeric_chat_id>", "messageId": "<message_id>", "message": "Updated text." }
```

Current OpenClaw resolves topic-qualified targets for edits. Still verify the
returned `messageId` and inspect topic placement when editing matters.

## Reply

```json
{
  "action": "send",
  "message": "Replying to that.",
  "replyTo": "<message_id>"
}
```

After callbacks, pass a verified real message ID or omit `replyTo`; callback
identifiers are not message IDs.

## Reaction

```json
{ "action": "react", "messageId": "<message_id>", "emoji": "👍" }
```

Use `"remove": true` to remove it. The supported Unicode set is runtime-owned;
`🦞` is not in Telegram's default reaction set.

## Media or file

```json
{ "action": "send", "media": "/absolute/path/to/file.png", "message": "Short caption", "forceDocument": true }
```

Omit `forceDocument` for an inline photo. Captions are not rich bodies; send
rich explanation separately. Forum-thumbnail images default to true 1:1.

## Sticker

```json
{
  "action": "sticker",
  "stickerId": ["<file_id>"]
}
```

```json
{
  "action": "sticker-search",
  "query": "cat waving",
  "limit": 5
}
```

Check `channels.telegram.actions.sticker` first. A sticker `file_id` is not a
custom emoji or topic-icon ID.

## Pin

```json
{
  "action": "send",
  "message": "Pinned announcement",
  "delivery": { "pin": true }
}
```

## Plugin-owned command buttons

This branch is only for deterministic plugin replies; ordinary assistant sends
use `presentation.blocks`.

```json
{
  "text": "Choose a report 👇\n\nOptions: 🖥️ Hardware · 🧰 Services",
  "channelData": {
    "telegram": {
      "buttons": [[
        { "text": "🖥️ Hardware", "callback_data": "/health hardware" },
        { "text": "🧰 Services", "callback_data": "/health services" }
      ]]
    }
  }
}
```

## Topic actions

Use [forum topics](telegram-forum-topics.md). Topic icon fields are
runtime-schema-gated; never invent a custom emoji ID or drop to a token-bearing
raw API command.
