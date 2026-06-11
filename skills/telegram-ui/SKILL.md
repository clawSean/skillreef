---
name: telegram-ui
description: "Telegram chat UI: inline buttons, URL buttons, selects, polls, formatting, edits, replies, reactions, stickers, media, and pins via OpenClaw Telegram integration. Use when sending any interactive or rich UI element on Telegram, including confirmations, games, wizards, polls, message edits, and media delivery."
---
# Telegram UI

Use this skill whenever sending interactive controls, rich formatting, polls, or media on Telegram through OpenClaw.

This skill is the self-contained Telegram UI command foundation. It should tell an agent which Telegram response controls are available, which OpenClaw fields to use, and which limitations to avoid without requiring another skill or procedure for core behavior.

---

## Available UI Commands

Use these working paths first:

| Need | Use |
|---|---|
| Normal message | `message` with `action: "send"` |
| Inline buttons | `message` with `action: "send"` and `presentation.blocks[].type: "buttons"` |
| Select-style choice | `message` with `presentation.blocks[].type: "select"`; Telegram renders it as buttons |
| Poll or vote | `message` with `action: "poll"` |
| Edit an existing bot message | `message` with `action: "edit"` and `messageId` |
| Reply to a specific message | `message` with `action: "send"` and `replyTo` |
| React without clutter | `message` with `action: "react"` |
| Send image, GIF, video, or file | `message` with `action: "send"` and `media` |
| Pin an important message | `message` with `action: "send"` and `delivery.pin: true` |
| Plugin-owned command menu | plugin response `channelData.telegram.buttons` |

Avoid these as primary paths:

- raw `buttons` parameter on `message` for Telegram
- CLI `--buttons`
- URL buttons through OpenClaw's presentation renderer
- Telegram MarkdownV2
- raw HTML outside the renderer whitelist in the Formatting section

---

## Quick Decision Rule

Before choosing the reply path:

- **Pure info** → plain text (markdown-ish)
- **Open-ended input needed** → plain text
- **2 to 6 discrete tap-friendly options** → inline buttons
- **7+ options from a known list** → buttons still work (Telegram has no native select dropdown — selects render as buttons)
- **Team pulse / voting** → native poll
- **Long content with emphasis** → markdown-ish formatting (bold, italic, code, lists)

A conversational suggestion list counts as a menu if the user is meant to pick from it.

---

## Formatting

OpenClaw converts markdown-ish text to Telegram HTML (`parse_mode: "HTML"`).

**What works in normal messages (markdown-ish → Telegram HTML):**
- `**bold**` or `__bold__` → renders bold (note: `__x__` is bold here, NOT underline)
- `_italic_` → renders italic
- `~~strikethrough~~` → renders strikethrough (`<s>`)
- `||spoiler||` → renders native Telegram spoiler (`<tg-spoiler>`) — tap to reveal
- `> quoted line` → renders native Telegram blockquote (`<blockquote>`)
- `` `inline code` `` → renders monospace
- ` ```lang\ncode\n``` ` → renders code block
- bullet lists, numbered lists → render as text lines
- links `[text](url)` → render as hyperlinks

*(strikethrough/spoiler/blockquote verified live 2026-06-10 — local docs at `docs/concepts/markdown-formatting.md` claiming spoilers are Signal-only are stale; the Telegram renderer passes `enableSpoilers: true`.)*

**Nesting & edits (verified live 2026-06-10):**
- Nesting works: bold/links inside spoilers, strike/spoilers inside blockquotes, bold+strike combos all render correctly
- `action=edit` preserves all formatting — edited messages re-render markdown-ish the same as sends
- ⚠️ **Spoiler link leak:** a `[link](url)` inside `||spoiler||` blurs the text but still generates a link preview card below the message, revealing the URL's destination. Don't put links in spoilers if the destination is the surprise.

**Raw HTML passthrough (whitelist only):**

OpenClaw's Telegram renderer **preserves** these raw HTML tags instead of escaping them:
`<b> <strong> <i> <em> <u> <ins> <s> <strike> <del> <code> <pre> <tg-spoiler> <blockquote>` plus attribute forms `<a href="...">`, `<span class="tg-spoiler">`, `<tg-emoji emoji-id="...">`, `<tg-time datetime="...">`.

Use raw HTML for the two things markdown-ish can't express:
- **Underline:** `<u>underlined</u>` (markdown `__x__` gives bold, not underline)
- **Date/time entity:** `<tg-time datetime="...">June 15</tg-time>` — ⚠️ API accepts the tag but it renders as **plain text** on iOS (verified via screenshot 2026-06-10). No date chip, no tap action. Don't bother — just write the date as text.

Any tag NOT on the whitelist (`<div>`, `<script>`, etc.) is escaped and leaks as literal text.

**Reading formatted inbound messages (what survives → agent):**
- ✅ `~~strikethrough~~`, `||spoiler||`, `[label](url)` links — arrive as markdown markers, readable
- ❌ blockquote formatting — arrives as plain text, no `>` prefix (can't tell it was a quote)
- ❌ date entities — arrive as the display text only (no datetime metadata)

**Tappable link rule:**
- Do not rely on bare URLs in Telegram status replies. If a link should be tappable, write it as a markdown link: `[Status page](https://example.com/status)`.
- For multiple links, use short labels instead of pasting raw URLs:
  - `[Day 1 — Overview](https://example.com/day1)`
  - `[Day 2 — Details](https://example.com/day2)`

**What does NOT work:**
- Raw HTML tags outside the whitelist above → escaped, leak as literal text
- `<blockquote expandable>` → attribute not whitelisted, gets escaped (plain `<blockquote>` or `>` works)
- Markdown tables → not supported, use bullets or plain text
- Headings (`#`) → stripped to plain text (headingStyle: none)

---

## Inline Buttons

### When to Use

**Hard rule:** if the user can answer by tapping one of **2 to 6 discrete options**, use inline buttons instead of a plain text menu.

Includes confirmations, "pick a lane" prompts, and short idea menus.

### Mobile Readability Rule

**Always mirror button options in the message text** because Telegram mobile may truncate or hide full button titles.

Pattern:
```
Pick a lane 👇

Options: ✅ Approve · ❌ Cancel · ⏰ Later
```

Then send the same choices as real inline buttons.

### Sending Buttons

**Only working path:** use the first-class `message` tool with `presentation.blocks` containing a `buttons` block with `value` (callback) buttons:

```json
{
  "action": "send",
  "channel": "telegram",
  "target": "<chat_id>",
  "message": "Question text 👇\n\nOptions: ✅ Yes · ❌ No",
  "presentation": {
    "blocks": [
      { "type": "text", "text": "Question text" },
      { "type": "buttons", "buttons": [
        { "label": "✅ Yes", "value": "yes", "style": "success" },
        { "label": "❌ No", "value": "no", "style": "danger" }
      ]}
    ]
  }
}
```

**⚠️ No CLI `--buttons` flag exists.** The CLI only supports `--presentation`. The raw `buttons` param on the message tool is not wired for Telegram either — only `presentation` delivers inline keyboards.

### URL Buttons

**⚠️ Broken in OpenClaw's renderer.** Telegram fully supports `InlineKeyboardButton` with `url`, but OpenClaw's `buildInlineKeyboard` filters through `button?.text && button?.callback_data`, silently dropping URL-only buttons.

**Workaround:** bypass OpenClaw and call the Telegram Bot API directly:

```python
import json, os, urllib.request

# Read token from environment (never print it)
token = os.environ["TELEGRAM_BOT_TOKEN"]

payload = {
    "chat_id": "<chat_id>",
    "text": "Message text",
    "reply_markup": {
        "inline_keyboard": [
            [
                {"text": "🌐 Edge", "url": "https://edge.app"},
                {"text": "📖 Support", "url": "https://support.edge.app"}
            ]
        ]
    }
}

req = urllib.request.Request(
    f"https://api.telegram.org/bot{token}/sendMessage",
    data=json.dumps(payload).encode(),
    headers={"Content-Type": "application/json"},
    method="POST"
)
result = json.loads(urllib.request.urlopen(req).read())
```

You can mix URL and callback buttons in the same keyboard — just use `url` for links and `callback_data` for actions. Telegram requires exactly one of the two per button.

For simple link needs without buttons, inline text links `[Edge](https://edge.app)` also work.

### Button Grid Layouts

Binary (same row):
```json
[[{"text":"✅ Yes","callback_data":"yes"},{"text":"❌ No","callback_data":"no"}]]
```

Binary + defer (two rows):
```json
[
  [{"text":"✅ Do it","callback_data":"yes"},{"text":"❌ Cancel","callback_data":"no"}],
  [{"text":"⏰ Not now","callback_data":"defer"}]
]
```

Three+ choices (stacked):
```json
[
  [{"text":"🔥 Now","callback_data":"now"}],
  [{"text":"⏰ Later","callback_data":"later"}],
  [{"text":"❌ Cancel","callback_data":"cancel"}]
]
```

### Callback Handling

When a user taps a callback button, it arrives as: `callback_data: <value>`

Proceed with the selected action. Never expose raw callback values as the primary UX — translate back to human-readable.

### Emoji Rule

**Always use emojis on button labels.** They make buttons scannable.

| Intent | Emoji |
|--------|-------|
| Yes / Approve | ✅ |
| No / Cancel | ❌ |
| Later / Defer | ⏰ |
| Danger / Destructive | ⚠️ |
| Info | ℹ️ |
| Lock in | 🔒 |
| Neutral A/B | 🅰️ 🅱️ |

---

## Selects (Presentation)

On Telegram, `presentation.blocks` selects render as inline buttons (Telegram has no native dropdown). Semantically useful for cross-platform portability and for fallback text generation.

```json
{
  "type": "select",
  "placeholder": "Choose lane",
  "options": [
    { "label": "🔐 Security", "value": "security" },
    { "label": "🦞 Product", "value": "product" }
  ]
}
```

Functionally identical to buttons on Telegram. Prefer buttons for Telegram-only flows; use selects when the same flow also targets Slack (where selects render as real dropdowns).

---

## Polls

Native Telegram polls. Use for voting, quizzes, or pulse checks.

```json
{
  "action": "poll",
  "channel": "telegram",
  "target": "<chat_id>",
  "pollQuestion": "Which approach?",
  "pollOption": ["Option A", "Option B", "Option C"],
  "pollAnonymous": false,
  "pollDurationSeconds": 300
}
```

Flags:
- `pollAnonymous` / `pollPublic` — visibility of voters
- `pollDurationSeconds` — auto-close (5–600)
- `pollMulti` — allow multiple selections

---

## Edits

Edit a previously sent message:

```json
{
  "action": "edit",
  "channel": "telegram",
  "target": "<chat_id>",
  "messageId": "<message_id>",
  "message": "Updated text here."
}
```

Useful for:
- Showing which button was selected after a tap
- Updating status messages
- Correcting typos

---

## Replies

Reply to a specific message using `replyTo`:

```json
{
  "action": "send",
  "channel": "telegram",
  "target": "<chat_id>",
  "message": "Replying to that ^",
  "replyTo": "<message_id>"
}
```

Telegram shows a native quote/link to the original message.

---

## Reactions

React to a message with an emoji:

```json
{
  "action": "react",
  "channel": "telegram",
  "target": "<chat_id>",
  "messageId": "<message_id>",
  "emoji": "👍"
}
```

Remove with `"remove": true`. Only unicode emoji supported (no custom emoji through this path).

---

## Media & Stickers

### Images / Files

```json
{
  "action": "send",
  "channel": "telegram",
  "target": "<chat_id>",
  "media": "/absolute/path/to/file.png",
  "message": "Caption text",
  "forceDocument": true
}
```

- `forceDocument: true` bypasses Telegram compression (sends as document)
- Without it, images get compressed and GIFs may be converted to video
- **Captions support full formatting** (bold, strike, spoiler, links — same markdown-ish renderer as message text; verified live 2026-06-10)

### Stickers

```json
{
  "action": "sticker",
  "channel": "telegram",
  "target": "<chat_id>",
  "stickerId": ["<fileId>"]
}
```

Search cached stickers:
```json
{
  "action": "sticker-search",
  "channel": "telegram",
  "query": "cat waving",
  "limit": 5
}
```

---

## Pins

Pin a message (bot must have pin permissions in groups):

```json
{
  "action": "send",
  "channel": "telegram",
  "target": "<chat_id>",
  "message": "Pinned announcement",
  "delivery": { "pin": true }
}
```

Or use `--pin` flag in CLI.

---

## Presentation Cards

OpenClaw `MessagePresentation` renders as: message text + inline keyboard on Telegram.

Supported blocks on Telegram:
- ✅ `text` → included in message body
- ✅ `context` → included in message body (no visual distinction from text)
- ⚠️ `divider` → not rendered (Telegram has no visual divider)
- ✅ `buttons` → inline keyboard
- ✅ `select` → inline keyboard (rendered as buttons)

`title` → prepended to message text.
`tone` → no visual effect on Telegram (matters for Slack/Teams).

**Important:** keep presentation text simple. Markdown-ish emphasis is the safest default in presentation text. Use raw HTML only when you need a whitelist-only feature from the Formatting section and have verified that exact send path.

---

## Repair Flow

If you realize you sent a plain-text menu that should have been buttons:
1. Acknowledge briefly.
2. Resend as buttons immediately.
3. Don't defend the mistake.

If buttons fail or are invisible:
1. Acknowledge briefly.
2. Restate options in plain text.
3. Continue from the user's typed choice.
4. Document the failure for the skill if it's a reusable issue.

---

## Callback Naming Convention

Use stable, lowercase snake_case callback values scoped to the flow:

- `game_challenge`, `game_authenticate`
- `triage_bug`, `triage_feature`
- `pd_edgespend`, `pd_cancel`
- Generic: `yes`, `no`, `cancel`, `defer`

Never surface raw callback tokens as the primary UX.

---

## What's NOT Available (Current Limitations)

- **URL link buttons via OpenClaw** — broken in renderer (`buildInlineKeyboard` drops buttons without `callback_data`). Direct Telegram Bot API workaround works — see URL Buttons section above.
- **Raw `buttons` param / CLI `--buttons`** — not wired for Telegram. Only `presentation.blocks.buttons` with `value` delivers inline keyboards.
- **WebApp buttons** — not exposed through OpenClaw message tool
- **Login buttons** — not exposed
- **Payment/Buy buttons** — not exposed
- **Copy-to-clipboard buttons** — not exposed
- **Reply keyboards** (custom keyboard replacing the system keyboard) — not exposed
- **Request contact/location buttons** — not exposed
- **Telegram MarkdownV2** — avoid; escaping is error-prone and OpenClaw uses HTML parse mode
- **Raw HTML outside the whitelist** — escaped by OpenClaw's renderer (see Formatting section for the allowed tags)
- **Inbound blockquote/date metadata** — formatting markers for quotes and `tg-time` entities are stripped on inbound; only the text arrives

These may become available in future OpenClaw versions.


## Plugin Reply Buttons (`channelData.telegram.buttons`)

For plugin command replies, there is a Telegram-specific path in addition to the normal `message` tool presentation path: a plugin handler can return `channelData.telegram.buttons` with Telegram-style rows of `{ text, callback_data }`. This is useful for no-LLM slash-command steering where the callback should re-enter the command path.

Example:

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

Use this for plugin-owned command menus only. For ordinary assistant sends with the `message` tool, keep using `presentation.blocks` buttons as documented above. Mirror the options in message text either way.
