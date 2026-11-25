---
name: discord-ui
description: Use for Discord replies, rich text and components, reactions, polls, media, threads/forums, and channel actions.
---

# Discord UI

Use on every Discord conversation. Match the room: concise in busy groups, richer
when a substantial answer benefits from structure. Discord is Markdown-native;
do not copy Telegram HTML or iMessage plain-text rules into it.

## Compose

1. Answer first. Use short paragraphs with blank lines, brief **bold** anchors,
   native headings (`##`/`###`) for substantial sections, lists for parallel
   items, and named links. Use `> ` for quotes, backticks/fences for exact code,
   and spoilers only when hiding content actually helps. Emoji add character,
   not visual clutter.
2. Keep tables narrow; Discord/mobile table rendering can be awkward. Prefer
   bullets for a small comparison. Wrap bare URLs in `<...>` to suppress embeds;
   use named Markdown links when the link deserves a label. OpenClaw suppresses
   link previews by default; opt in only when the preview is useful.
3. For direct responses, ordinary final delivery is enough. In an ambiguous
   conversation, use an explicit native reply (`replyTo` or `[[reply_to:<id>]]`)
   rather than quoting the person's message. Reaction-only acknowledgment is
   fine when no text answer is needed.

## Pick the native interaction

- **Thread:** Start one when a topic needs sustained work, many updates, a
  separate audience, or a durable home. Check the parent channel and current
  `message` schema; use `thread-create` with a descriptive title and initial
  message, then `thread-reply` or send to `channel:<threadId>`. Forum/media
  parents accept posts as threads, not ordinary messages. Read
  [threads and forums](references/threads-and-forums.md) for routing details.
- **Choices:** Use Components v2 buttons/selects for a small interactive
  decision; use a native poll for group voting. Text must still state the
  choices and outcome. A component callback is time-limited (30 minutes by
  default), so do not present it as permanent. For complex input, use a modal
  only when the active tool exposes it. See [rich actions](references/rich-actions.md).
- **Media:** Send actual attachments with `message`; a local artifact path or
  Markdown link is not delivery. Verify a returned message ID. Use captions
  and media galleries when they improve comprehension.
- **Housekeeping:** Use native edit for evolving status, pins for lasting
  reference, reactions for acknowledgment, and search/read for context. Use
  channel/server administration only when the user asked for it.

## Capability and delivery gate

The tool schema, action gate, Discord channel permissions, and current account
all matter. Before an uncommon action, inspect `message` action/schema and
`permissions` for the target channel; a grant in one server does not transfer
to another. Do not infer UI rendering or button callbacks from a send receipt.
Check readback, and inspect the client for visual claims when available. A send
without a message ID is unconfirmed; inspect before retrying to avoid duplicates.

Use [capability map](references/capability-map.md) for the action inventory and
local proof/gap notes. Installed OpenClaw docs at
`~/.npm-global/lib/node_modules/openclaw/docs/channels/discord/`
are the current runtime authority; recheck them when a behavior changes.
