# Telegram Rich Rendering Matrix

Evidence for Telegram Bot API 10.3 rich bodies when
`channels.telegram.richMessages: true`. Operating rules live only in
`SKILL.md`; client diagnosis lives in `rich-message-client-compat.md`.

## Current calibrated surface

- OpenClaw: 2026.9.1
- Client: native Telegram for macOS 12.9 build 282526
- Surface: a private test group forum topic
- Date: 2026-09-04; spacing density revalidated 2026-09-07
- Additional coverage: the reviewer's post-2026-07-19 Telegram iOS client; exact build
  was not recorded.

## Capability evidence

| Capability | State | Evidence / boundary |
| --- | --- | --- |
| headings | pass | Native styled heading on calibrated rich clients |
| details/summary | pass | T1/T6-era iOS proof and macOS message 4308 |
| checkbox tasks | pass | macOS message 4308 |
| mark, sup, sub | pass | iOS 2026-07-05 |
| math inline/block | pass | iOS 2026-07-05 |
| divider, quote+citation, aside, footer | pass | iOS 2026-07-05 |
| ordered-list start/reversed | pass | iOS 2026-07-05 |
| image, figure/caption | pass | iOS 2026-07-05; HTTPS block media only |
| collage/slideshow | pass | iOS 2026-07-05 |
| map, video, audio | pass | iOS 2026-07-05; HTTPS block media only |
| custom emoji | pass | known-good ID confirmed by the reviewer 2026-07-29 |
| named anchors/jump links | pass | iOS 2026-07-05 |
| Markdown table | conditional pass | 5×3 plain table complete on macOS message 4309 |
| raw HTML table | conditional pass | caption + two rows complete on macOS message 4311 |
| Copy Text presentation action | unavailable | absent from installed 2026.9.1 schema; dry run rejected 2026-09-04 |

## Current layout proof

### T9–T13: spacing and prose-list markers

- T9 (message 4316) mixed list paths and showed source blank lines collapsing;
  it was useful for discovery, not a final marker comparison.
- T10 (message 4320) compared Markdown blank lines, adjacent paragraph blocks,
  an nbsp spacer paragraph, and `<br><br>`. Only `<br><br>` produced the reviewer's
  requested visible blank line on native macOS 12.9.
- T11 (message 4324) was invalid: mixed raw break tags prevented its Markdown
  lane from parsing as a semantic list.
- T12 isolated paths, but its low-resolution capture did not justify a verdict
  about the literal `•` glyph.
- T13 compared a semantic rich list (message 4336) with literal `•` prose blocks
  (message 4337) using the same body font and text. Retina inspection showed the
  literal glyph baseline-aligned while the semantic marker sat high.

Observed result: literal `•` aligned in ordinary prose/status blocks. Semantic
`ul`/`ol` retained hanging indentation, and checkbox lists rendered task state.

### T14–T15: production composition and block boundaries

- T14/T15 (messages 4382–4383) were invalid composition tests. Inline
  `<br><br>` immediately after headings kept later HTML islands inside the
  heading block, so `details`, `table`, and break tags leaked visibly. This was
  authoring failure, not evidence that rich mode was off.
- T14B (message 4384) used source blank lines to end block structures and a
  standalone `<br><br>` paragraph between top-level blocks. Retina inspection
  proved baseline-aligned literal bullets, a working details block, and
  checked/unchecked task controls; T17D later superseded its spacing conclusion.
- T15B (message 4385) used the same boundaries. Retina inspection proved the
  complete captioned 2-column/3-row table and its collapsible row mirror.
- Screenshots: failed authoring (local evidence),
  corrected collapsed view (local evidence),
  expanded structure proof (local evidence),
  and expanded table mirror (local evidence).

Observed result: source blank lines terminated headings and block islands.
Inline concatenation caused the leaked tags in 4382–4383; T17D later showed that
standalone break paragraphs compound spacing and are not a spacing primitive.

### T17: compact, spacious, and paragraph density

- T17A (message 4403) kept three short literal-bullet items adjacent with one
  inline `<br>`.
- T17B (message 4404) separated two multi-sentence bullets with inline
  `<br><br>`; T17C (message 4405) used the same form between prose paragraphs.
  Each rendered exactly one empty visual row.
- T17D (message 4406) isolated the old standalone `<br><br>` paragraph between
  separate prose blocks. It produced the oversized compounded gap visible in
  the reviewer's screenshot and is not suitable for prose/list spacing.
- Screenshots: T17A–C density proof (local evidence)
  and T17D standalone control (local evidence).

Observed result: one newline or inline `<br>` gives compact adjacent lines;
inline `<br><br>` gives one empty visual row; a standalone break paragraph
compounds the gap. This test established spacing mechanics only; T18–T19 later
superseded its item-level density policy.

### T18–T20: authored lines and whole-list density

- T18C (message 4415) failed because both long single-sentence bullets wrapped
  while the list stayed compact. T18D (message 4416) passed because its
  multi-line bullets were spaced.
- T18F (message 4418) failed because it mixed compact and spacious separators
  inside one list. Density must remain consistent throughout a contiguous list.
- T18G (message 4419) and the Markdown-only T18I control (message 4421) failed:
  every authored prose line needs one empty visual row even when it continues
  the same thought.
- T19A–D (messages 4425–4428) isolated the accepted replacements: space a list
  when most items are multi-line, keep it compact when most are single-line,
  apply that density to every item, and space every authored prose line.
- T19E/T19F (messages 4429–4430) compared the unresolved 50/50 boundary;
  spacious is the accepted conservative fallback.
- T20A/T20B (messages 4459–4460) isolated the refined line threshold: predicted
  one- and two-line items stayed compact, while predicted three-plus-line items
  used one spacious density across the list.

Observed result: sentence count does not determine density. At normal target
width, classify likely one- and two-line items as compact and likely
three-plus-line items as long; use roughly 100–120 visible characters or 16–20
ordinary words when direct rendering is unavailable, and count borderline items
as compact. Choose one density by whole-list majority; a 50/50 tie remains
spacious. The reviewer reviewed these topic messages directly; local Retina capture was
unavailable because the Mac display was locked.

### T21: soft-newline paragraph indent

- Production message 4461 used a source newline immediately after each inline
  `<br><br>`; the reviewer's screenshot in reply 4462 showed the first visual line of
  each following paragraph indented by one ordinary space.
- An installed-renderer A/B mapped `Alpha<br><br>\\nBeta` to
  `Alpha\\n\\n Beta`, while source-adjacent `Alpha<br><br>Beta` mapped to
  `Alpha\\n\\nBeta`. Outbound controls are messages 4464–4465.
- Independent native-client capture was unavailable because no computer-capable
  node was connected; T17C already visually passed the source-adjacent form.

Observed result: a Markdown soft newline after inline break tags survives as one
leading space. Keep the following prose source-adjacent to `<br><br>`.

## Table history and battery

### Historical failure

In ClawShop on OpenClaw 2026.7.1, a 5-column/3-row Markdown table reached the
renderer with every row intact, but an unrecorded client displayed one body row.
Bold and inline code inside cells were present but were never isolated as the
cause. This proves tables are not portable across unknown clients.

### T7 regression battery

Record OpenClaw version, rich-message state, client platform/version/build,
chat surface, message IDs, and Retina screenshots.

1. **T7a — plain:** 5 columns, header, 3 body rows, plain cells. Pass only when
   every row/cell is visible and horizontal scrolling works where required.
2. **T7b — formatting isolation:** repeat T7a with bold in row one and inline
   code values. Diagnostic only; compare with T7a.
3. **T7c — raw HTML:** caption, two headers, three plain rows. Pass only when no
   markup leaks and every row is visible.

## Structure regression battery

Send each probe separately. Do not combine Markdown and raw HTML lanes.

1. **T1 paragraphs:** three Markdown paragraphs separated by blank source lines.
2. **T2a bullets:** three Markdown `-` items.
3. **T2b numbers:** three Markdown numbered items in a separate message.
4. **T3 newlines:** three lines separated by single literal newlines.
5. **T4 paragraph blocks:** three adjacent `p` blocks. Diagnostic only; current
   rich HTML treats `p` as transparent rather than a dependable spacing island.
6. **T5 breaks:** `line1<br>line2<br/>line3`, then a separate `<br><br>` gap
   comparison. Expect no leaked tags and the intended visual gap.
7. **T6 combined structure:** heading, details, checkbox list, and a plain prose
   block; verify every block independently.
8. **T13 marker A/B:** semantic `ul` and literal `•` in separate same-font
   messages with identical text.

## Dead or failed features

- `tg-time` with `datetime` leaked raw markup in the 2026-07-05 iOS audit. The
  distinct legacy `unix` form was not tested in that run.
- `tg-reference` and Markdown footnotes leaked literal text.
- `figure` with a `tg-spoiler` attribute did not blur the image.
- Expandable blockquotes did not collapse in the rich-body audit; `details` was
  separately observed working.

## Evidence discipline

A successful API response proves delivery, not visual rendering. Change an
operating rule only after exact-client inspection. Keep dated outcomes here;
do not duplicate them in `SKILL.md` or the compatibility guide.
