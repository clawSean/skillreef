---
name: "telegram-ui"
description: "Use for every Telegram reply, control, poll, reaction, media send, topic action, or rendering repair; produce readable rich output."
---

# Telegram UI

After compaction or resume, re-read this before any substantial Telegram final.
Use it on the first pass for every visible Telegram message. Reading is not completion;
do not add a second model pass.

## 1. Read the current surface

1. Treat injected Telegram `response_format` as runtime authority for rich state,
   supported blocks, math, media, and markup.
2. If absent, inspect the selected account's `channels.telegram.richMessages`;
   never infer it from another account.
3. With rich on, ordinary finals and `message` text use the default
   Markdown-to-rich-block path. Legacy HTML and captions remain separate.

- **This workspace:** ❔ not determined — check the setting in your config, then update this line. <!-- LOCAL-STATUS -->
See the [rendering matrix](references/rich-rendering-matrix.md) for dated
calibration. If runtime conflicts, follow runtime and rerun the matching canary
before changing rules.

## 2. Choose the delivery path

- **Ordinary conversation:** use the standard final path; manually sending then
  suppressing it can bypass reply-time TTS. Inline breaks are route-scoped:
  use `<br>` or `<br><br>` only when that exact path passes a canary. Source
  blank lines do not guarantee visual air; use semantic lists for literal rows.
- **Controls/actions:** use `message` for controls, edits, files, media, topics,
  or out-of-band sends. Verify the active schema;
  keep bodies portable unless a rich island helps.
- **Copy control:** use `message.presentation.blocks` for a schema-exposed
  clipboard action.

## 3. Compose the body

### Structure and spacing

- **Hard default: every authored prose paragraph or thought break gets one empty
  visual row.** On a calibrated path, use source-adjacent `<br><br>`; plain
  `\n\n` is not a visual separator. Client wrapping needs no markup.
- Pick each separator by boundary:
  - `heading/block ↔ body`: real source blank line for syntax only; rely on the
    block's native spacing and do not add `<br><br>`.
  - `prose → prose`: `First.<br><br>Next paragraph.`
  - `literal list → prose`: `Last item.<br><br>Next paragraph.`
  - `literal item → literal item`: the list-wide density below.
- Multiple headings are fine; each starts at start or after real `\n\n`.
  Never emit `<br><br>###`; end prior block first. Keep `<br><br>` away from block-level HTML islands.
- Never send prose paragraphs separated only by source blank lines. In rich
  `message` sends, keep each prose break source-adjacent to `<br><br>`.
- On a break-canary path, separate literal `•` rows with the density rule's
  source-adjacent inline breaks; bare source newlines can collapse and are never
  separators. Otherwise use source paragraphs. Never use one `<br>` for prose or
  block boundaries, a standalone `<br><br>` paragraph, or spacer entities.
- Use literal `•` prose/status rows with inline breaks for calibrated baseline
  alignment; do not substitute Markdown `-` during repairs. Reserve semantic lists
  for nesting, tasks, or runtime requirements.
- Literal lists are compact by default. If every item is **90 visible characters
  or fewer**, use one source-adjacent `<br>` between items. If any item exceeds
  90, use `<br><br>` between every item. Count rendered characters, including
  spaces but excluding formatting syntax and URL destinations. This proxies an
  item wrapping beyond two typical mobile lines.

### Scanability

- Use medium emoji density and one in each button label.
- A standalone prose title is a native `###` heading, not bold alone. Follow it
  with one source blank line for syntax, relying on native heading spacing; never
  add `<br>`. Limit bold to 1–3 inline scan
  anchors under 20% of body words; never bold whole paragraphs or lists.
- Use inline code for simple one-line values, never newline/escape-sequence
  examples: the latter leaked backticks in a client canary. Use prose or fenced
  code for those examples; use named links for navigation.
- **Rich by default:** use as many supported features as fit—headings, lists,
  quotes, details, tables, dividers, links, controls, decorative blocks. No
  numeric cap; maximize useful variety.

### Copyability

- Treat exact values as copyable.
- For 1–256 characters, keep the answer rich and send a separate legacy
  inline-code companion with native `📋 Copy`. Prefer typed `copy-text`;
  otherwise use the local token resolver without exposing the token.
- Above 256, send exact text alone as a separate legacy message for whole-message
  **Copy**; no rich/code blocks. Files are only for artifacts.
- Never fake Copy with a callback, split values, or expose secrets.
  Shapes and fallback: [payload recipes](references/payload-recipes.md).

### Tables

- Use tables only when comparison benefits; prefer narrow two-column tables on
  mobile. Unknown surfaces use compact items until their table canary passes.
- Keep cells plain unless formatting is proven. Every operational table needs a
  complete row-for-row compact mirror; show it directly if rendering fails.
  Diagnosis/fallback: [client compatibility](references/rich-message-client-compat.md).

## 4. Choose the interaction

Use a reaction for acknowledgement, `replyTo` for a specific message, buttons
for choices, a poll for a vote, edit for prior status, and pin for important
output. Never replace discrete buttons with a plain-text menu. Group/topic Mini
Apps use a direct-link URL plus browser fallback; true `web-app` is private-chat
only after surface proof.

Use typed actions inside `presentation.blocks`; top-level `buttons` are stripped.
Mirror choices in the message. Open
[payload recipes](references/payload-recipes.md) for exact schemas and limits.

## 5. Handle media and special branches

- Captions are short Markdown-ish bodies with literal line breaks; send rich
  explanation separately.
- Forum/topic thumbnails default to true 1:1 with the subject in a centered
  safe area unless another ratio is requested.
- Prefer the injected voice transcript. If absent, say so and follow the active
  `voice-conversation` transcript-repair guidance; never pretend to hear it.
- Keep sticker, custom-emoji, and forum-topic icon IDs distinct.
- Open only the active specialty branch: [admin controls](references/telegram-admin-control.md),
  [forum topics](references/telegram-forum-topics.md), or
  [Mini Apps](references/telegram-mini-apps.md).
- For renderer problems use [client compatibility](references/rich-message-client-compat.md);
  for dated proof/canaries use the [rendering matrix](references/rich-rendering-matrix.md).

## 6. Verify delivery and renderer claims

Use first-pass composition, not a manual checklist or second model review.

1. For actions, confirm the active schema supports them and the delivery result
   contains a real message ID.
2. For renderer-sensitive work, inspect the actual client and record client,
   version/build, surface, message ID, and screenshot in the rendering matrix.
   Tests/receipts are not visual proof. If inspection is blocked, say unverified.
3. If wrong, acknowledge and repair once; suspend the failing feature on that
   surface until its canary passes.

## Reference boundary

`SKILL.md` owns common send-time behavior. Exact action payloads live in
[payload recipes](references/payload-recipes.md); diagnosis in
[client compatibility](references/rich-message-client-compat.md); evidence in
the [rendering matrix](references/rich-rendering-matrix.md); rare branches in
[admin controls](references/telegram-admin-control.md),
[forum topics](references/telegram-forum-topics.md), and
[Mini Apps](references/telegram-mini-apps.md). `scripts/test.sh` validates the
bundle. Keep dated evidence out of operating rules; change a rule only after a
controlled canary establishes durable behavior.
