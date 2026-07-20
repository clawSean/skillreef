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

## Structure collapse — FIXED on calibrated iOS client (2026-07-20); Desktop/Web unverified

**History:** OpenClaw's markdown→rich pipeline (`markdownToTelegramRichHtml`) emits plain `\n` between paragraphs/list items, and Telegram's rich HTML renderer used to collapse literal newlines like a browser (root-caused 2026-07-05). That forced the explicit-HTML-blocks-only regime.

**2026-07-20 rebase (T1–T6 screenshot battery, JPop's iOS after Telegram app update):**
- ✅ Markdown paragraphs separated by blank lines render as separate paragraphs with natural air (T1)
- ✅ Markdown `-` bullets and `1.` numbered lists render one item per line with list margins (T2)
- ✅ Single bare `\n` renders as a line break (T3)
- ✅ Bare `<p>` blocks now get real vertical margins — one blank-line-equivalent gap, JPop's preferred air (T4, T6)
- 🚫 `<p>&#160;</p>` nbsp spacer now DOUBLE-pads (own blank line + p margins) — visibly fatter gap than bare `<p>` (T5, T6; JPop flagged the overkill). Spacer and its variants (`<br>&#160;<br>`, `&#10240;`) are retired.
- ✅ `<br/>` no longer leaks as literal text — renders as a break (T5). `<br>` remains the canonical form.
- Empty `<p></p>` still appears IGNORED (T4/T6 gaps identical with and without it) — medium confidence.

**Caveat:** the fix is in the Telegram CLIENT renderer, not OpenClaw's pipeline (which still emits bare `\n`). Recipients on stale clients may still see run-on text — if reported, fall back to explicit HTML blocks for that surface and log the case in `rich-message-client-compat.md`. Coverage: iOS = full T1–T6 battery; **macOS Desktop = partial** (markdown paragraph structure + air + bold + inline code confirmed 2026-07-20 via self-captured node screenshot of live DM messages; spacer-delta and full battery still pending); Web unverified.

**Re-running the battery** (after a major OpenClaw upgrade or Telegram client change). Record alongside the results: OpenClaw version · `channels.telegram.richMessages` state · Telegram client platform + app version/build · surface (DM/group/topic) · one screenshot per probe. (2026-07-20 run gap: iOS app version/build not recorded — capture it next time.) Send each probe as its own message with the exact body shown (`\n` = literal newline):

- T1 (markdown paragraphs): `First paragraph.\n\nSecond paragraph.\n\nThird paragraph.` → expect three separate paragraphs with air
- T2a (bullets): `- alpha\n- beta\n- gamma` → expect one item per line with list margins
- T2b (numbered list, separate message): `1. one\n2. two\n3. three` → expect numbered items one per line (kept separate from T2a so blank-line behavior between list types isn't conflated with item behavior)
- T3 (bare newlines): `line one\nline two\nline three` → expect three lines
- T4 (bare p + empty p): `<p>A</p><p>B</p><p></p><p>C</p>` → expect natural gaps; empty `<p></p>` adds nothing
- T5a (nbsp spacer): `<p>A</p><p>&#160;</p><p>B</p>` → expect spacer gap FATTER than T4's natural gap (validates spacer stays retired)
- T5b (br forms): `line1<br>line2<br/>line3` → expect two line breaks, no literal `br/` leak (validates `<br/>` handling only)
- T6 (side-by-side calibration): one message containing both a bare-p gap and an nbsp-spacer gap → direct comparison screenshot

## Other verified quirks

- **Escaped entities double-decode (2026-07-05):** writing `&lt;details&gt;` (even inside `<code>`) renders as NOTHING — entities decode back to a real tag and the sanitizer strips it. Mention tag names without angle brackets.
- **Inbound echo blindness (2026-07-04):** replies quoting our rich sends arrive as `[unsupported Telegram rich_message received]` — we cannot read our own rich bodies back.
- **Spoiler link bleed (re-tested 2026-07-05, rich mode):** `||spoiler with link||` shows no preview card in rich mode; in normal/non-rich mode a preview card DID appear (2026-06-10) — treat spoiler links as leaky in normal mode.
