---
name: telegram-ui
description: "Telegram chat UI: inline buttons, URL buttons, selects, polls, formatting, edits, replies, reactions, stickers, media, and pins via OpenClaw Telegram integration. Use when sending any interactive or rich UI element on Telegram, including confirmations, games, wizards, polls, message edits, and media delivery."
---
# Telegram UI

Use this skill whenever sending interactive controls, rich formatting, polls, or media on Telegram through OpenClaw.

For cross-platform orchestration of multi-step flows, also use `skills/interactive-sessions/SKILL.md`.

## ✅ Pre-Send Checklist — every send, no exceptions

1. **Structure:** explicit HTML blocks — `<p>`, `<ul><li>`/`<ol><li>`, `<br>` (NEVER `<br/>`). Newlines, blank lines, `•` bullets, and markdown lists all collapse into run-on text in rich mode.
2. **Air:** `<p>&#160;</p>` spacer between consecutive prose `<p>` blocks. Lists/tables/headings self-space — no spacer around them.
3. **Emoji:** medium-to-high density in every message and every button label. A flat, emoji-less message is a defect.
4. **Controls:** 2–6 discrete options → inline buttons (plain-text menus are FORBIDDEN) · acknowledging → reaction · answering a specific message → `replyTo` · group vote → poll · status update on a prior send → edit it in place · must stay findable → pin.
5. **Richness floor:** content-heavy send (status, comparison, summary, multi-part) → at least TWO rich blocks from the Toolchest. Short conversational quips are exempt — don't force a table onto "yep, done ✅".
6. **Media send?** Captions are NOT rich-body — HTML blocks leak as literal tags there. Short markdown-ish caption on the image; rich body goes in a separate text message. (Media section below.)
7. **Game / Mini App link?** Primary button = BotFather direct link (`https://t.me/<bot>/<app>?startapp=…`) — works in groups, opens natively. Browser URL is the fallback button, never the primary. (Buttons section below.)

Botched a send? → Repair Flow below: acknowledge briefly, resend right, don't defend it.

## 🧰 Toolchest — Full Vocabulary (scan before every send)

This skill exists partly to keep the WHOLE toolbox in working memory — the natural failure mode is falling back to plain text and forgetting 80% of these exist. Sweeping this list before composing is BINDING, not advisory: every send gets a deliberate pick. If your last several messages were all plain text, you've stopped scanning — course-correct immediately.

- **Controls & actions (always available):** callback buttons · URL buttons · WebApp buttons · selects · polls · reactions (stack them) · replies (`replyTo`) · edits · pins · stickers · media/captions · voice notes · mentions
- **Inline styling (always available):** bold · italic · underline (`<u>`) · strikethrough · `||spoiler||` · inline code · code blocks · `[links](url)` · `> blockquote`
- **Rich body blocks (ONLY when Local Status below says ON):** `##` headings · markdown-pipe tables · `<details><summary>` collapsibles · checkbox task lists · `<mark>` highlights · `<sup>`/`<sub>` · `<tg-math>`/`<tg-math-block>` formulas · `<hr>` dividers · `<blockquote>`+`<cite>` · `<aside>` pull quotes · `<footer>` fine print · `<ol start>`/`<ol reversed>` · `<img>` image blocks · `<figure>`+`<figcaption>` captioned images · `<tg-collage>` image grids · `<tg-slideshow>` swipe galleries · `<tg-map>` inline maps · `<video>`/`<audio>` inline players · `<tg-emoji>` custom emoji · named anchors + `#` jump links
- **Dead — never use:** `<tg-time>` (leaks raw markup) · footnotes (`<tg-reference>` and markdown `[^1]` both leak) · `<blockquote expandable>` (never collapses — use `<details>`) · raw HTML `<table>` in group-visible sends (leaks on some clients — markdown-pipe instead) · `tg-spoiler` attr on `<figure>` (no-op)

Match content to block: comparative data → table (or compact list) · long optional detail/logs/fine print → collapsible · multi-section → headings + dividers · checklist status → checkbox list, not ✅/❌ prose · key line → `<mark>` or `<aside>` · quotes → `<blockquote>`+`<cite>` · formulas → math blocks · 2+ images → collage/slideshow · single image with context → `<figure>`+caption · location → map · hosted video/audio → inline players.

Per-element verification evidence, dates, and quirks: `references/rich-rendering-matrix.md`.

## 🧱 Three Layers (don't conflate)

1. **Formatting layer** — markdown-ish text → Telegram HTML (`## Formatting` below). Always on.
2. **UI controls layer** — `message.presentation.blocks` → inline keyboards, selects, portable fallback. Canonical path for buttons/controls.
3. **Rich body layer** — `channels.telegram.richMessages: true` → Telegram Bot API 10.1 `rich_message` sends/edits: native rich body rendering. **Config-gated: only use rich blocks when the Local Status entry below says ON.** It upgrades the message BODY only — it does NOT replace presentation, polls, reactions, pins, or any control above. **Group/topic fallback:** if a surface renders `this message is not supported in your version of Telegram`, send normal Telegram HTML there until clients catch up; log the case in `references/rich-message-client-compat.md`.

**⚙️ Rich messages — Local Status**

Setting: `channels.telegram.richMessages` in the OpenClaw config (check via `gateway config.get` or `openclaw.json`). If it isn't `true`, skip the rich body layer entirely — normal Telegram HTML + presentation blocks only.

- **This workspace:** ❔ not determined — check the setting in your config, then update this line. <!-- LOCAL-STATUS -->

## ⚖️ House Rules — MANDATORY (canonical copy; other sections point here)

The Pre-Send Checklist is the enforcement summary; these are the mechanics behind it.

**Structure & spacing (rich mode):**
- OpenClaw's markdown→rich pipeline emits bare newlines between blocks and Telegram's rich renderer collapses them like a browser — explicit HTML blocks are the ONLY reliable structure (upstream bug; root cause in the matrix ref).
- `<br/>` gets escaped by the sanitizer; always `<br>`.
- Bare `<p>` gives a new line but no vertical air; empty `<p></p>` is IGNORED. Canonical spacer: `<p>&#160;</p>` between consecutive prose paragraphs — JPop has flagged missing air more than once. House shape: intro `<p>` → spacer → body `<p>`/lists → spacer → wrap-up `<p>`.
- Inline markdown (`**bold**`, `_italic_`, `` `code` ``, links) still works in rich mode — the collapse only hits block structure.
- To mention an HTML tag by name in a body, write it WITHOUT angle brackets (e.g. `details` in code style) — escaped entities double-decode and the sanitizer strips the resulting tag, rendering NOTHING.

**Tables:**
- Preferred path: **markdown-pipe tables** — render as native rich tables incl. horizontal scroll on mobile. Put the most important columns first (off-screen columns need a swipe).
- Raw HTML `<table>` and fancy table attrs are path-sensitive (leaked as literal markup cross-client) — never group-visible. Details in the matrix ref.
- Operationally important table → mirror the key result in prose before/after it. If a table leaks: resend as markdown-pipe or compact list, then log the case.

**Buttons:**
- Presentation buttons auto-chunk 3 per row and iOS truncates long labels in 3-button rows — keep labels ≲12 chars when sending 3+ buttons (e.g. "✅ All good", not "✅ All render clean").
- Every button label gets an emoji.

**Operational gotchas:**
- **Inbound echo blindness:** replies quoting our rich sends arrive as `[unsupported Telegram rich_message received]` — never rely on reply-quote content for context; use message ids.
- **Edit in forum topics:** `action=edit` rejects `telegram:<id>:topic:<n>` targets ("recipient must be a numeric chat ID") — pass the bare numeric group id + `messageId`.
- **Send after a callback tap:** auto-reply may default to the huge callback message id and fail with "replyTo must be a positive integer" — pass an explicit real `replyTo` (or none via a fresh target).

## Quick Decision Rule

Before choosing the reply path:

- **Short conversational reply** → prose (still HTML-block structured + emojis) — the ONLY case where prose alone is fine
- **Pure info, content-heavy** → prose PLUS rich blocks (≥2 — see checklist floor)
- **Open-ended input needed** → prose question
- **2 to 6 discrete tap-friendly options** → inline buttons
- **7+ options from a known list** → buttons still work (Telegram has no native select dropdown — selects render as buttons)
- **Team pulse / voting** → native poll
- **Long content with emphasis** → headings + tables + collapsibles + inline styling, not a wall of bold text

A conversational suggestion list counts as a menu if the user is meant to pick from it.

---

## Formatting

⚠️ **Rich-mode override:** everything below about inline styling still applies, but when rich mode is ON, body STRUCTURE must come from explicit HTML blocks — see **House Rules** above.

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
- ✅ **Spoiler link bleed re-tested 2026-07-05 (rich mode):** `||spoiler text including a link||` — no link preview card appeared below the message. The destination stayed hidden. (Prior note from 2026-06-10 said a preview card DID appear; that was in normal/non-rich mode. Rich mode appears to suppress the preview card. In normal mode, treat spoiler links as leaky and add explicit `<meta name="twitter:card" ...>` or just avoid linking the sensitive URL directly.)

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
- Markdown tables in **legacy normal mode** → not supported, use bullets or plain text. With `richMessages: true`, markdown-pipe tables are the preferred native-table path; see **House Rules → Tables** above.
- Headings (`#`) → stripped to plain text (headingStyle: none)

---

## 🎛️ Action Rules (binding per-tool rules — JSON payloads live in `references/payload-recipes.md`)

**Mentions:** prefer `replyTo` context → `tg://user?id=` HTML mention → `@username` → plain name (never invent IDs). Tag once where it routes/assigns/credits attention, not every sentence.

**Buttons:**
- Canonical path: `presentation.blocks` buttons block — kinds: `value` (callback), `url` (link), `webApp.url`. Mixing URL + callback in one keyboard works.
- 🚨 Top-level `buttons` param is silently STRIPPED by the MCP schema — send returns ok, no keyboard renders. `presentation.blocks` only. (CLI likewise: `--presentation`, there is no `--buttons` flag.)
- ⚠️ `presentation` does not replace `message`: body goes in `message`, keyboard ONLY in presentation — presentation-only sends error, duplicated body text double-renders.
- Mirror the options in the message text — mobile truncates button titles.
- **Mini Apps work in groups AND DMs — proven live in a group 2026-07-09 (Claw Four).** Launch hierarchy: groups/topics → primary button is a normal `url` button to the BotFather direct link (`https://t.me/<bot>/<app>?startapp=…`), which still opens natively as the Mini App, + browser fallback. DMs and surfaces proven to render it → true `webApp` button preferred. The only DM-ish limit is the true `webApp` BUTTON KIND, which Telegram drops from unproven group keyboards — never conclude "web apps don't work in groups."
- Callback values: stable lowercase snake_case scoped to the flow (`triage_bug`, `yes`, `defer`); never surface raw tokens as the primary UX.

**Selects:** render as buttons on Telegram (no native dropdown) — prefer buttons; use selects only when the same flow targets Slack.

**Polls:** `action=poll` — flags: `pollAnonymous`/`pollPublic`, `pollMulti`, `pollDurationSeconds` (5–600 auto-close).

**Reactions:** `action=react` (+ `remove: true`). Unicode-only, supported set: 👍 ❤️ 🔥 🎉 🤩 😱 😁 😢 💩 🤮 🤯 😴 🤬 🤡 😇 🤝 ✍️ 👀 🫡 — 🦞 does NOT work. Stack generously; reactions are free acknowledgment.

**Edits:** `action=edit` + `messageId` — show the tapped choice, update status in place, fix typos. (Forum-topic edit gotcha in House Rules.)

**Voice notes IN:** Telegram doesn't pass audio files through — only stubs arrive. Say so immediately ("can't hear audio — what'd you say?") and prompt a text resend; never pretend to process.

**Media:** `media=/abs/path` + `message` as caption. ⚠️ **Captions are NOT rich-body:** media sends bypass the rich_message path, so explicit HTML blocks (`<p>`, `<ul><li>`, spacers) leak as literal tags in captions (seen live 2026-07-10, JoeBot Demo). Captions take markdown-ish inline formatting + real line breaks only. If the update needs rich blocks, send the image (short plain caption) and the rich body as a separate message. `forceDocument: true` = no compression, sends as document; OMIT it for tappable inline photos.

**Stickers:** `action=sticker` with `stickerId`; find ids via `action=sticker-search`.

**Pins:** `delivery: { pin: true }` on the send (bot needs pin permission in groups).

**Presentation cards:** block text must stay plain/portable — raw HTML in presentation blocks leaks as literal text. `divider`/`tone` are no-ops on Telegram; `title` prepends to the body.

---

## Group Final Delivery

In Telegram groups, normal final assistant replies can silently fail to post (long-standing regression, upstream `#76424`). **Always deliver group-visible output with explicit `message(action="send")`** — never rely on the final answer being auto-delivered.

## Repair Flow

- Sent a plain-text menu that should've been buttons? → acknowledge briefly, resend as buttons, don't defend it.
- Buttons failed/invisible? → acknowledge, restate options in plain text, continue from the typed choice, and document the failure here if reusable.

## What's NOT Available

- Login, payment, copy-to-clipboard, request-contact/location buttons; reply keyboards (system-keyboard replacement) — not exposed
- Telegram MarkdownV2 — avoid; OpenClaw uses HTML parse mode
- Raw HTML outside the whitelist — escaped (see Formatting)
- Inbound blockquote/date metadata — stripped on inbound; only text arrives
- Plugin-owned command menus have a separate `channelData.telegram.buttons` path — recipe in `references/payload-recipes.md`

## Group Admin / Control Actions

For rare group-level control actions — changing the group profile photo, checking bot admin permissions, raw Bot API methods not exposed by the `message` tool — use `references/telegram-admin-control.md`.

For forum topic management — creating topics, renaming them, posting into a topic via `threadId` — use `references/telegram-forum-topics.md` (`topic-create`, `topic-edit`; needs the Manage Topics admin permission).

For Telegram Mini Apps / games — direct-link anatomy, BotFather ownership split, launch-card rules — use `references/telegram-mini-apps.md`; the game apps themselves live in `~/projects/openclaw-game-night/`.

Only on explicit ask or when the requested workflow clearly needs it; these mutate group state, so verify permissions and report the exact result.
