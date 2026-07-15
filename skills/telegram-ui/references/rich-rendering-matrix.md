# Rich Body Rendering Matrix — Verification Detail

Per-element verification record for Telegram Bot API 10.1 `rich_message` bodies via OpenClaw (`channels.telegram.richMessages: true`). The working vocabulary lives in SKILL.md's Toolchest; this file holds the evidence, dates, and quirks. Client-specific setup/compat debugging: `rich-message-client-compat.md`.

## Verified working

- ✅ **Markdown-pipe tables** — preferred table path. JPop verified three patterns in a private test group on 2026-07-06: simple 3-column, wider 5-column mobile-scroll, and an operator-card pattern with the key result mirrored in prose first. Nick confirmed the same probe rendered in Dev Team on 2026-07-06.
- ✅ Collapsible `<details><summary>` (tappable chevron)
- ✅ `<mark>` highlight (yellow), `<sup>`/`<sub>`
- ✅ Headings (`##` → large styled heading)
- ✅ Task lists: `<ul><li><input type="checkbox" checked/> item</li></ul>` → native checked/unchecked boxes
- ✅ Formulas: `<tg-math>E = mc^2</tg-math>` inline; `<tg-math-block>…</tg-math-block>` display math (beautifully typeset, verified 2026-07-05)
- ✅ Standalone image blocks: `<img src="https://..."/>`
- ✅ `<hr>` divider · `<blockquote>` with `<cite>` (citation renders gray under the quote) · `<aside>` pull quote (bordered callout) · `<footer>` (small gray line) — all verified 2026-07-05
- ✅ `<ol start="5">` numbered-list offset · `<ol reversed>` countdown ordering (verified 2026-07-05)
- ✅ `<figure><img …/><figcaption>…</figcaption></figure>` — image with gray caption (verified 2026-07-05)
- ✅ `<tg-collage>` of `<img>` blocks — native grid (1 big + rest tiled); `<tg-slideshow>` — swipeable gallery with dot indicator (both verified 2026-07-05)
- ✅ `<tg-map lat="…" long="…" zoom="…"/>` — real inline map tile with pin (verified 2026-07-05)
- ✅ `<video src="https://…"/>` inline playable video · `<audio src="https://…"/>` audio player with duration (both verified 2026-07-05)
- ✅ `<tg-emoji emoji-id="…">` custom emoji — renders as custom sticker (falls back to the Unicode emoji if the id is unrecognized; verified 2026-07-05)
- ✅ `<a name="…">` named anchors + in-message `href="#…"` jump links — anchor set and tap-to-jump both work (verified 2026-07-05)
- ✅ `valign`/`rowspan` table attrs — merged/aligned rendering verified 2026-07-05 on iOS, but see the raw-table warning below before using them group-visible.
- ✅ Mixed URL + callback presentation keyboards (JPop tap, 2026-07-04)

## Dead / broken — never use

- ❌ `<blockquote expandable>` — renders as a normal OPEN blockquote on iOS, no collapse (verified 2026-07-05). Use `<details><summary>`.
- ❌ `<tg-time>` — fully dead on iOS (all forms verified 2026-07-05): `unix=` with empty content renders nothing; `unix=` with inner fallback shows only the plain fallback; `datetime=` LEAKS RAW MARKUP. Write times as plain text with an explicit timezone.
- ❌ `figure tg-spoiler` attr — does NOT blur the image, no effect (verified 2026-07-05). For image spoilers use `<tg-spoiler>` wrapping or `||…||` for text.
- ❌ `<tg-reference name="…" type="footnote">` — leaks as raw markup (tag not whitelisted; verified 2026-07-05). Markdown footnotes `[^1]` also leak as literal text. No working footnote syntax found yet.

## Raw HTML tables — path-sensitive, unsafe group-visible

Raw HTML `<table bordered="true" striped="true">…</table>` leaked as literal/collapsed markup for Nick in Dev Team on 2026-07-05 across Telegram Desktop latest, recently updated mobile, and Telegram Web — a cross-client raw-table renderer/sanitizer failure, not a single-client issue. Earlier iOS successes (incl. `<caption>`, `colspan`, `align` extras verified 2026-07-04/05) are path-specific, not a general guarantee. Until the renderer path is fixed: markdown-pipe tables only for group-visible sends.

## Structure collapse — root cause (2026-07-05)

OpenClaw's markdown→rich pipeline (`markdownToTelegramRichHtml`) emits plain `\n` between paragraphs/list items, and Telegram's rich HTML renderer collapses literal newlines like a browser. Markdown blank lines and `-` lists do NOT fix it — verified live, both render run-on. Only explicit HTML blocks (`<p>`, `<ul><li>`, `<ol><li>`, `<br>`) create structure. `<br/>` gets escaped by the sanitizer — must be `<br>`. This is an OpenClaw bug worth an upstream fix (newlines should become `<br>`/`<p>` in the rich HTML build).

## Spacing verification (screenshots, 2026-07-05)

`<p>` gives each paragraph its own line but only modest vertical air on iOS (≈ a `<br>` gap); `<ul>`/`<ol>` lists get natural margins. Empty `<p></p>` padding blocks are IGNORED, but a paragraph holding an invisible character renders as a REAL blank line. Canonical spacer: `<p>&#160;</p>` (nbsp). `<br>&#160;<br>` inline and `&#10240;` braille-blank also verified working.

## Other verified quirks

- **Escaped entities double-decode (2026-07-05):** writing `&lt;details&gt;` (even inside `<code>`) renders as NOTHING — entities decode back to a real tag and the sanitizer strips it. Mention tag names without angle brackets.
- **Inbound echo blindness (2026-07-04):** replies quoting our rich sends arrive as `[unsupported Telegram rich_message received]` — we cannot read our own rich bodies back.
- **Spoiler link bleed (re-tested 2026-07-05, rich mode):** `||spoiler with link||` shows no preview card in rich mode; in normal/non-rich mode a preview card DID appear (2026-06-10) — treat spoiler links as leaky in normal mode.
