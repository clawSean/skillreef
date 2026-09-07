---
name: "telegram-ui"
description: "Use for every Telegram reply, control, poll, reaction, media send, topic action, or rendering repair; produce readable rich output."
---

# Telegram UI

Use this runbook for every Telegram turn. Keep the common path here; open a
reference only when its branch is active.

## 1. Read the current surface

1. Treat the injected Telegram `response_format` as the runtime authority for
   rich ON/OFF state, supported blocks, math syntax, media rules, and markup.
2. If that context is absent, inspect the selected account's
   `channels.telegram.richMessages`; never infer it from another account.
3. With rich mode on, ordinary final replies and explicit `message` text bodies
   use the default Markdown-to-rich-block path; no separate rich flag is needed.
   Caller-authored legacy HTML and media captions remain separate paths.

- **This workspace:** ❔ not determined — check the setting in your config, then update this line. <!-- LOCAL-STATUS -->
The [rendering matrix](references/rich-rendering-matrix.md) owns the latest
dated client, runtime, and surface calibration.

If the runtime contract conflicts with this dated calibration, follow the
runtime contract and re-run the relevant canary in
[rendering matrix](references/rich-rendering-matrix.md) before changing a
production rule.

## 2. Choose the delivery path

- **Ordinary conversational text:** use OpenClaw's standard final-reply path.
- **Controls or channel actions:** use `message` for buttons, polls, reactions,
  edits, pins, stickers, files, media, topics, or an intentional out-of-band
  send. Keep control-message bodies to portable Markdown unless they genuinely
  need a rich structural island; then obey the block-boundary rules below.
- **Copy button required:** use `message.presentation.blocks` only when the
  active schema exposes a real clipboard action.
- Never manually send an ordinary reply and then suppress the final; that can
  bypass reply-time features such as inbound-triggered TTS.

## 3. Compose the body

### Structure and spacing

- Pick each separator by boundary:
  - `heading/block → body`: real source blank line.
  - `prose/literal list → prose`: inline `<br><br>` after the final item. Keep
    following text on the same physical source line with no intervening whitespace:
    `Last item.<br><br>Next paragraph.`
  - `list item → list item`: the list-wide density below.
- Never glue `<br><br>` to headings or block-level HTML islands such as tables
  and details; it can trap later markup and leak tags.
- In prose, inline `<br><br>` at every intentional authored line or paragraph
  break renders one empty visual row. Automatic Telegram wrapping needs no markup.
  Example: `First.<br><br>**Next:**`. Source blank lines and adjacent `p` blocks
  do not reliably create visible air.
- A single newline or inline `<br>` gives no empty row; reserve it for compact
  list items. Never put a standalone `<br><br>` paragraph between prose blocks;
  it creates an oversized gap. Do not use nbsp or other spacer entities.
- Use a literal `•` inside the rich body for ordinary prose/status lists. It
  remains rich messaging and is baseline-aligned on the calibrated client.
- Choose one density for each contiguous list and use it between every item.
  At normal Telegram width, classify likely 1–2 rendered lines as compact and
  likely 3+ as long. Without direct rendering, use roughly 100–120 visible
  characters or 16–20 ordinary words as a three-line proxy; ignore markup and
  count borderline items as compact. When more than half are long,
  separate every item with inline `<br><br>`; when more than half are compact,
  keep every item compact with one newline or inline `<br>`. Use spacious
  density for a 50/50 list tie. Sentence count never decides density. Evaluate
  separate or nested lists independently. Use semantic Markdown/`ul` lists
  only when hanging indentation or structure matters; use checkbox lists for
  tasks.

### Scanability

- Use medium-to-high emoji density and an emoji in every button label.
- A short standalone line that titles the prose below is a native `###` heading,
  not bold alone; follow it with a real source blank line, never `<br>`. Reserve
  bold for 1–3 inline scan anchors under 20% of body words, never whole
  paragraphs or lists.
- Put exact reusable values in inline code. Use named Markdown links rather than
  bare URLs when navigation is the goal.
- For a content-heavy send, choose at least two purposeful structures from the
  injected rich toolset—such as a heading plus details, a checklist plus a
  divider, or a table plus its accessible mirror. Do not add decorative blocks
  that make the answer harder to scan.

### Copyability

- When the user may need to type, paste, save, compare, or reuse an exact value,
  show it in inline code and add a real `📋 Copy` button when the active
  presentation schema supports one. Telegram copy text accepts 1–256 characters.
- Probe the active schema for a typed `copy-text` action before promising the
  button. Treat support as volatile; keep the latest dated local proof in the
  [rendering matrix](references/rich-rendering-matrix.md).
- Never fake Copy with a callback and never build a raw token-bearing Bot API
  command as a workaround. If no real clipboard action is exposed, keep the
  exact visible fallback and say the Copy button is runtime-blocked when its
  absence matters.
- For values over 256 characters, use a code block plus a reusable file or other
  exact artifact; do not truncate the copy target.

### Tables

- Use a table only when it materially clarifies repeated fields or comparisons.
  Dense inventories should use a narrow two-column table on mobile.
- Rich tables are client/surface-conditional. The calibrated macOS forum topic
  passed both Markdown and raw HTML tables; unknown surfaces use compact items
  until the matching T7 canary passes.
- Keep cells plain unless a formatting-isolation canary passed. Put emphasis and
  copyable values outside the table.
- Every operational table needs a complete row-for-row compact mirror. Put the
  mirror in a collapsible detail when the table renders; show it directly if the
  table truncates, leaks markup, or produces an unsupported-message fallback.

## 4. Choose the interaction

| Need | Telegram action |
| --- | --- |
| acknowledge only | reaction |
| answer a specific message | `replyTo` |
| 2–6 discrete choices | inline buttons; never a plain-text menu |
| 7+ known choices | buttons; Telegram has no native select dropdown |
| team pulse or vote | native poll |
| update prior status | edit in place |
| keep important output findable | pin |
| group/topic Mini App | BotFather direct-link URL button + browser fallback |
| private-chat Mini App | true `web-app` button after surface proof |

Use typed actions inside `presentation.blocks`. Top-level `buttons` are stripped.
Mirror button choices in the message because mobile labels can truncate. Never
use a true `web-app` action in a group; use the direct-link URL action instead.

Exact payloads: [payload recipes](references/payload-recipes.md).

## 5. Handle media and special branches

- Captions are not rich bodies. Use short Markdown-ish captions with literal
  line breaks; send rich explanatory content as a separate text message.
- In forum/topic-enabled groups, generate group-thumbnail images as true 1:1
  squares with the focal subject in a centered safe area unless another aspect
  ratio is explicitly requested.
- Prefer the injected transcript for inbound voice. If no transcript exists,
  say so and follow the `voice-conversation` skill's
  transcript-repair path;
  never pretend to hear it.
- Keep sticker IDs, custom emoji IDs, and forum-topic icon IDs distinct.
- Open specialty references only for the requested branch:
  - admin/group mutations: [admin controls](references/telegram-admin-control.md)
  - forum topics: [forum topics](references/telegram-forum-topics.md)
  - Mini Apps: [Mini Apps](references/telegram-mini-apps.md)

Current control payloads are in [payload recipes](references/payload-recipes.md).
Client diagnosis is in [client compatibility](references/rich-message-client-compat.md);
dated visual proof and regression batteries are in the
[rendering matrix](references/rich-rendering-matrix.md).

## 6. Verify before claiming success

1. Re-read the final body for source-safe block boundaries, heading hierarchy,
   authored-line spacing, consistent list-wide density, literal prose bullets,
   working links, and exact-value fallbacks.
2. Confirm the chosen action exists in the active `message` schema and that the
   returned delivery result contains a real message ID.
3. For renderer-sensitive work, inspect the actual Telegram client—not merely
   the outbound payload. Record client, version/build, chat surface, message ID,
   and screenshot in the rendering matrix.
4. If a send is wrong, acknowledge briefly and repair once: resend missing table
   rows as compact items, restate invisible buttons in text, and suspend the
   failing feature on that surface until its canary passes.

## Reference boundary

- `SKILL.md`: send-time behavior only.
- [Payload recipes](references/payload-recipes.md): copyable typed payloads and
  action-specific constraints.
- [Rendering matrix](references/rich-rendering-matrix.md): evidence, message IDs,
  and canaries.
- [Client compatibility](references/rich-message-client-compat.md): diagnosis
  and fallback selection.
- Specialty references: rare admin, topic, and Mini App branches.
- `scripts/test.sh`: fail-closed structural validation.

Do not copy dated evidence back into the operating rules. Change a rule only
when a controlled canary establishes a new durable behavior.
