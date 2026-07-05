---
name: telegram-ui
description: "Telegram chat UI: inline buttons, URL buttons, selects, polls, formatting, edits, replies, reactions, stickers, media, and pins via OpenClaw Telegram integration. Use when sending any interactive or rich UI element on Telegram, including confirmations, games, wizards, polls, message edits, and media delivery."
---
# Telegram UI

Use this skill whenever sending interactive controls, rich formatting, polls, or media on Telegram through OpenClaw.

For cross-platform orchestration of multi-step flows, also use `skills/interactive-sessions/SKILL.md`.

## 🧰 Full Toolbox — Scan Before Every Send

This skill exists partly to keep the WHOLE toolbox in working memory — the natural failure mode is falling back to plain text and forgetting 80% of these exist. Before composing any Telegram reply, mentally sweep the full list and pick deliberately:

**callback buttons · URL buttons · WebApp buttons · selects · polls · reactions (stack them) · replies (`replyTo`) · edits · pins · stickers · media/captions · mentions · spoilers · blockquotes · rich messages (Bot API 10.1 body rendering)**

If your last several messages were all plain text, that's a signal you've stopped scanning — course-correct.

## 🧱 Three Layers (don't conflate)

1. **Formatting layer** — markdown-ish text → Telegram HTML (`## Formatting` below). Always on.
2. **UI controls layer** — `message.presentation.blocks` → inline keyboards, selects, portable fallback. Canonical path for buttons/controls.
3. **Rich body layer** — `channels.telegram.richMessages: true` → Telegram Bot API 10.1 `rich_message` sends/edits: richer native body rendering, incl. native-ish tables. **Enabled on this box 2026-07-04 (experimental).** It upgrades the message BODY only — it does NOT replace presentation, polls, reactions, pins, or any control above. Prefer exercising it for content-heavy sends (tables, structured docs) and report rendering quirks; some Telegram clients may still show rich messages as unsupported. If a send renders broken for JPop, fall back to normal formatting and log the case here.

**Rich body rendering matrix — live-verified on iOS via JPop screenshots (2026-07-04):**
- ✅ Native tables (markdown `|` tables → real table blocks; wide tables scroll horizontally on mobile — verified, columns aren't lost — but keep key info in the first 2 columns since off-screen columns need a swipe)
- ✅ Collapsible `<details><summary>` (tappable chevron)
- ✅ `<mark>` highlight (yellow), `<sup>`/`<sub>`
- ✅ Headings (`##` → large styled heading)
- ✅ Task lists: `<ul><li><input type="checkbox" checked/> item</li></ul>` → native checked/unchecked boxes
- ✅ Formulas: `<tg-math>E = mc^2</tg-math>` → real typeset math
- ✅ Standalone image blocks: `<img src="https://..."/>`
- ❌ Markdown footnotes `[^1]` — leak as literal text; don't use until a working syntax is found
- 🚨 **LINE BREAKS COLLAPSE (root-caused 2026-07-05):** OpenClaw's markdown→rich pipeline (`markdownToTelegramRichHtml`) emits plain `\n` between paragraphs/list items, and Telegram's rich HTML renderer collapses literal newlines like a browser. Markdown blank lines and `-` lists do NOT fix it — verified live, both still render run-on. **The only reliable structure in rich mode is explicit HTML blocks:** `<p>…</p>` paragraphs, `<ul><li>`/`<ol><li>` lists, `<br>` breaks (⚠️ must be `<br>`, NOT `<br/>` — the self-closing form gets escaped by the sanitizer). Headings/tables/details/math are block elements and are safe. This is an OpenClaw bug worth an upstream fix (newlines should become `<br>`/`<p>` in the rich HTML build).

**Verified gotchas with richMessages ON (2026-07-04):**
- ⚠️ **Inbound echo blindness:** when someone replies to one of our sends, the quoted message arrives to the agent as `[unsupported Telegram rich_message received]` — we cannot read our own rich bodies back. Don't rely on reply-quote content for context; use message ids.
- ⚠️ **Edit in forum topics:** `action=edit` rejects `telegram:<id>:topic:<n>` targets ("recipient must be a numeric chat ID") — pass the bare numeric group id + `messageId`.
- ⚠️ **Send after a callback tap:** auto-reply may default to the huge callback message id and fail with "replyTo must be a positive integer" — pass an explicit `replyTo` to a real message id (or none via a fresh target).
- ✅ Mixed URL + callback presentation keyboards confirmed live (JPop tap, 2026-07-04).

**House style (binding rules — rich-mode authoring, updated 2026-07-05):**
- Medium-to-high emoji density on every message
- **Structure comes from explicit HTML blocks, never newlines:** wrap every paragraph in `<p>…</p>`, every list in `<ul><li>…</li></ul>` or `<ol><li>`, force a break with `<br>` (NEVER `<br/>` — the self-closing form gets escaped)
- Newlines, blank lines, `•` bullets, and markdown `-`/`1.` lists ALL collapse into run-on text in rich mode — verified live 2026-07-05; do not use them for body structure
- Inline markdown still works fine (`**bold**`, `_italic_`, `` `code` ``, links) — the collapse only hits block structure
- Reach for rich blocks when they add value: tables, `<details>`, `<mark>`, `<sup>`, `<tg-math>`, checkbox lists, headings, `<img>`
- **Spacing reality (verified via screenshots 2026-07-05):** `<p>` gives each paragraph its own line but only modest vertical air on iOS (≈ a `<br>` gap); `<ul>`/`<ol>` lists get natural margins. Empty `<p></p>` padding blocks are IGNORED, but a paragraph holding an invisible character renders as a REAL blank line — canonical spacer: `<p>&#160;</p>` (nbsp; `<br>&#160;<br>` inline and `&#10240;` braille-blank also verified). **JPop wants paragraphs air-separated: put `<p>&#160;</p>` between consecutive `<p>` blocks in normal prose messages.** Lists already carry their own margins — no spacer needed around `<ul>`/`<ol>`. House shape: intro `<p>` → spacer → `<p>`/lists → spacer → wrap-up `<p>`.
- **Button label length:** presentation buttons auto-chunk 3 per row and iOS truncates long labels in 3-button rows — keep labels ≲12 chars when sending 3+ buttons (e.g. "✅ All good", not "✅ All render clean")

---

## ⛔ Rich by Default — MANDATORY (HARD RULES, NOT TIPS)

These are binding requirements for every Telegram interaction — not "bias toward" suggestions. A plain, low-effort message where one of these applies is a defect: fix it on the spot (see Repair Flow).

**You MUST default to rich UI:**
- **Inline buttons are REQUIRED** for any Y/N or A/B/C prompt. A plain-text "would you like me to proceed?" is FORBIDDEN — send tappable options instead. 2–6 discrete options ⇒ buttons, always.
- **Reactions are REQUIRED** to acknowledge — don't burn a whole message on "got it".
- **Replies (`replyTo`) are REQUIRED** when answering a specific earlier message, so context threads.
- **Polls are REQUIRED** for group votes or multi-option decisions — never collect votes in prose.
- **Pins are REQUIRED** for announcements that must stay findable.
- **Edits are REQUIRED** for status updates — edit the original in place; don't spam follow-ups.
- **Stickers** when the vibe calls for it.

**Quick rules — apply on every send, no exceptions:**
- 2–6 options? → **buttons** (never a plain-text menu)
- Acknowledging? → **reaction**
- Replying to a specific message? → **`replyTo`**
- Vote / multi-option decision? → **poll**
- Important / must stay findable? → **pin**
- Status update on a prior message? → **edit the original**

**Emoji density — NON-NEGOTIABLE:** Use emojis heavily. Every message carries medium-to-high emoji density, every button label gets an emoji, and reactions are used freely. A flat, emoji-less Telegram message is wrong. (This mirrors the hard emoji mandate in `AGENTS.md`.)

**House-style formatting — MANDATORY:** Every message body is structured with explicit HTML blocks (`<p>` paragraphs, `<ul>/<ol>` lists, `<br>` breaks — never `<br/>`), medium-to-high emoji density. Newlines and markdown lists do NOT create structure in rich mode. These are requirements, not preferences. (Full mechanics in the house-style block at the top and the 🚨 gotcha in Three Layers.)

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

⚠️ **Rich-mode override (while `richMessages: true`, since 2026-07-04):** everything below about inline styling still applies, but body STRUCTURE must come from explicit HTML blocks (`<p>`, `<ul><li>`, `<br>`) — plain newlines and markdown lists collapse. See the house-style block at the top.

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
- Do not rely on bare URLs in Telegram status replies. If a link should be tappable, write it as a markdown link: `[Ravello page](https://example.com/?date=2026-05-16)`.
- For multiple links, use short labels instead of pasting raw URLs:
  - `[May 16 — Ravello](https://example.com/?date=2026-05-16)`
  - `[May 18 — Capri](https://example.com/?date=2026-05-18)`

**What does NOT work:**
- Raw HTML tags outside the whitelist above → escaped, leak as literal text
- `<blockquote expandable>` → attribute not whitelisted, gets escaped (plain `<blockquote>` or `>` works)
- Markdown tables → not supported, use bullets or plain text
- Headings (`#`) → stripped to plain text (headingStyle: none)

---

## User Mentions / Tagging

When referencing a specific Telegram user in a group, default to a real Telegram mention tag instead of writing only their plain name.

Preferred order:
- **Reply context first:** if responding to a specific message from that person, use `replyTo` so Telegram creates the native reply link.
- **User ID mention:** when you know the numeric Telegram user ID, write an HTML mention link: `<a href="tg://user?id=8681554364">Nick</a>`.
- **Username mention:** when you know their public username and do not have the numeric ID, use `@username`.
- **Plain name fallback:** only use a plain name when no user ID or username is available. Do not invent IDs or usernames.

Examples:
```json
{
  "action": "send",
  "channel": "telegram",
  "target": "telegram:<group_chat_id>",
  "message": "<a href=\"tg://user?id=8681554364\">Nick</a> this one is yours."
}
```

```json
{
  "action": "send",
  "channel": "telegram",
  "target": "telegram:<group_chat_id>",
  "message": "Looping <a href=\"tg://user?id=123456789\">JPop</a> in here."
}
```

Notes:
- `tg://user?id=<id>` mention links work through OpenClaw because raw `<a href="...">` is preserved by the Telegram HTML renderer.
- Escape or simplify display names before putting them inside the `<a>` tag; avoid raw `<`, `>`, or `&` in the visible label.
- In group chats, use mention tags whenever the message asks for, assigns, credits, or redirects attention to a person.
- Do not tag users gratuitously in every sentence. Tag once where it helps notification/routing, then use normal prose.
- If the user ID comes from trusted runtime metadata or contact/group memory, it is safe to use. If the identity is uncertain, say so or use the plain-name fallback.

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

**Canonical path:** use the first-class `message` tool with `presentation.blocks` containing a `buttons` block. Buttons support three kinds — `value` (callback), `url` (link), and `webApp.url` (Telegram WebApp):

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

**Raw `buttons` param also works** (`buttons=[[{text, callback_data, url?, web_app?, style?}]]`) — the Telegram renderer resolves explicit `buttons` first, then `presentation`. Prefer `presentation` for portability and fallback-text generation; the raw param is fine for quick Telegram-only sends. The CLI has no `--buttons` flag — CLI sends use `--presentation`.

### URL Buttons

**✅ Supported natively — verified LIVE 2026-07-04** (JPop-confirmed mixed URL + callback keyboard; earlier "broken in renderer" claims are stale — `toInlineKeyboardButton` handles `url`, `callback_data`, and `web_app`). Just put `url` on a presentation button:

```json
{ "type": "buttons", "buttons": [
  { "label": "🌐 Edge", "url": "https://edge.app" },
  { "label": "✅ Approve", "value": "approve", "style": "success" }
]}
```

You can mix URL and callback buttons in the same keyboard. Telegram requires exactly one target per button (url / callback / webApp). For simple link needs without buttons, inline text links `[Edge](https://edge.app)` also work.

**✅ Live-verified 2026-07-04** (private test group): mixed keyboard with 2 URL + 2 callback buttons rendered correctly and the callback delivered (`test2_ok`).

### WebApp Buttons

**✅ Exposed via presentation** — `{ "label": "🎮 Open App", "webApp": { "url": "https://..." } }` (legacy `web_app` also accepted). ⚠️ Telegram itself only shows WebApp buttons in **private chats** — in groups they're dropped by Telegram, not by OpenClaw. **Live-verified 2026-07-04:** sent to JPop's DM, button rendered and opened the URL in Telegram's in-app webview.

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

**Supported reaction emoji:** 👍 ❤️ 🔥 🎉 🤩 😱 😁 😢 💩 🤮 🤯 😴 🤬 🤡 😇 🤝 ✍️ 👀 🫡

**Rules:**
- React generously — stack multiple reactions on a message when it fits the vibe
- 🦞 does NOT work in the default reaction set (tested & failed 2026-02-13)
- Reactions are free acknowledgment; use them liberally instead of burning a whole message

---

## Voice / Audio Messages

Telegram does not pass audio files through to the agent — only metadata/stubs arrive.

**Rule:** When a voice message arrives, respond immediately: "Can't hear audio messages — Telegram doesn't pass the file through to me. What'd you say?" Don't attempt to process. Prompt a text resend.

*(Learned 2026-03-23 — Ingest group incident)*

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

**Important:** keep presentation text plain/portable. Do not use raw HTML tags in presentation blocks — they will be escaped and leak as literal text.

---

## Group Final Delivery

In Telegram groups, normal final assistant replies can silently fail to post (long-standing regression, upstream `#76424`). **Always deliver group-visible output with explicit `message(action="send")`** — never rely on the final answer being auto-delivered. ⏳ Re-verification scheduled after the 2026-07-04 richMessages rollout (along with media gotchas + voice-message limitation below).

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

- **CLI `--buttons` flag** — doesn't exist; CLI sends use `--presentation` (the tool-side raw `buttons` param DOES work — see Sending Buttons)
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


## Group Admin / Control Actions

Most Telegram work in this skill is message UI: formatting, buttons, polls, replies, media, reactions, edits, pins, and stickers.

For rare group-level control actions such as changing a group profile photo, checking bot admin permissions, or using Telegram Bot API methods not exposed by the `message` tool, use `references/telegram-admin-control.md`.

Do this only when the user explicitly asks or the operation is clearly part of the requested Telegram group workflow. These actions can mutate group state, so verify permissions and report the exact result.
