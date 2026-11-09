---
name: "telegram-ui"
description: "Use for Telegram replies, controls, polls, reactions, media, topics, and rendering repair."
---

# Telegram

After compaction/resume, re-read before a substantial final. Use on the first
pass for every Telegram message; reading is not completion. **Ordinary finals:
never emit `<br>` or `<br><br>`; they have leaked literally on iOS.**

## 1. Read the current surface

1. Treat injected Telegram `response_format` as runtime authority for rich state,
   supported blocks, math, media, and markup.
2. If absent, inspect the selected account's `channels.telegram.richMessages`;
   never infer it from another account.
3. With rich on, finals and `message` use Markdown-to-rich blocks. Legacy HTML
   and captions remain separate.

- **This workspace:** ❔ not determined — check the setting in your config, then update this line. <!-- LOCAL-STATUS -->
See the [rendering matrix](references/rich-rendering-matrix.md). If runtime conflicts,
follow runtime and rerun the canary.

## 2. Choose the delivery path

- **One compact block:** use the standard final path. It preserves reply-time
  TTS. Never use inline breaks on ordinary finals: that route failed on iOS.
- **Two or more visual blocks:** use `message(action="send")` on the calibrated
  rich route and finish without duplicating the reply in an ordinary final.
  This includes multiple prose paragraphs, prose plus a list, or long list
  items that need a visible blank line. Source blanks in ordinary finals
  collapse on iOS; break tags there leak literally. Readability takes priority
  over reply-time TTS here unless hands-free voice mode is active.
- **Controls/actions:** use `message` for controls, edits, media, topics, or
  out-of-band sends. Verify the active schema.
- **Copy:** use Telegram `copyTextButtons` only when exposed; never use shared
  presentation.

## 3. Compose the body

### Structure and spacing

- **Prioritize readable gaps.** For prose paragraphs on the calibrated explicit
  `message` rich-text path, use source-adjacent `<br><br>`; plain source blank
  lines collapse visually. Ordinary finals must not use break tags. Route any
  multi-block text through calibrated `message` when a visible gap matters.
- Before writing headings, literal bullets, or code, follow the exact boundary
  and no-leak rules in [rendering guardrails](references/rendering-guardrails.md).

### Scanability

- Use emojis; one per button.
- A standalone prose title is a native `###` heading, not bold alone. Follow it
  with one source blank line for syntax, relying on native heading spacing. Limit bold to 1–3 inline scan
  anchors under 20% of body words; never bold whole paragraphs or lists.
- Use inline code for simple one-line values; use prose or fenced code for
  newline/escape-sequence examples. Use named links for navigation.
- **Rich by default:** use as many supported features as fit—headings, lists,
  quotes, details, tables, dividers, links, controls, decorative blocks. No
  numeric cap; maximize useful variety.

### Copyability

- Treat exact values as copyable.
- For 1–256 characters, keep the answer rich and add `copyTextButtons` when the
  active schema exposes it; preserve the exact value, one button per row.
- Otherwise, send exact text as a separate plain message for whole-message
  **Copy**. Do not call the Bot API.
- Never fake Copy with a callback, split values, or expose secrets.
  Shapes and fallback: [payload recipes](references/payload-recipes.md).

### Tables

- Use tables only when comparison benefits; prefer narrow two-column tables on
  mobile. Unknown surfaces use compact items until their table canary passes.
- Keep cells plain unless formatting is proven. Every operational table needs a
  complete row-for-row compact mirror; show it directly if rendering fails.
  Diagnosis/fallback: [client compatibility](references/rich-message-client-compat.md).

## 4. Choose the interaction

Use a reaction to acknowledge, `replyTo` to target, edit for status, and pin for
key output. Controls are required when supported: confirmation requests
get confirm and decline/hold buttons; **2–5 discrete choices** get one button
each (or a poll for voting); text meant to be copied gets the Copy control above.
Mirror controls in text. Never replace buttons with a
plain-text menu. Hands-free voice mode remains button-free. Group/topic Mini
Apps use a direct-link URL plus browser fallback; true `web-app` is private-chat
only after surface proof.

Use typed actions inside `presentation.blocks`; top-level `buttons` are stripped.
Only agent callbacks use the recipe's legacy `value` until the typed canary
  passes. `copyTextButtons` is separate. Mirror choices in
  text. See [payload recipes](references/payload-recipes.md).

## 5. Handle media and special branches

- Captions are short Markdown-ish bodies with literal line breaks.
- Forum/topic thumbnails default to true 1:1 with the subject in a centered
  safe area unless another ratio is requested.
- Prefer the injected voice transcript. If absent, say so and follow the active
  `voice-conversation` transcript-repair guidance; never pretend to hear it.
- Keep sticker, custom-emoji, and forum-topic icon IDs distinct.
- Open only the active specialty branch: [admin controls](references/telegram-admin-control.md),
  [forum topics](references/telegram-forum-topics.md), or
  [Mini Apps](references/telegram-mini-apps.md).
- Renderer problems: [client compatibility](references/rich-message-client-compat.md);
  proof: [rendering matrix](references/rich-rendering-matrix.md).

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

Details: [rendering guardrails](references/rendering-guardrails.md), [payloads](references/payload-recipes.md), [compatibility](references/rich-message-client-compat.md),
[evidence](references/rich-rendering-matrix.md), [admin](references/telegram-admin-control.md),
[topics](references/telegram-forum-topics.md), [Mini Apps](references/telegram-mini-apps.md).
`scripts/test.sh` validates. Keep rules undated; require canary proof.
