# Rich actions

- `components` creates Discord Components v2 cards. Supported blocks include
  text, section, separator, actions, media-gallery, and file. One action row
  holds up to five buttons or one select. Selects can target strings, users,
  roles, mentionables, or channels. Buttons can use emoji or be links.
- Use `allowedUsers` on sensitive buttons. Component callbacks are single-use
  by default; `reusable: true` allows repeat interactions until expiry. The
  default callback lifetime is 30 minutes (configurable to at most 24 hours).
- `components.modal` can collect up to five text/checkbox/radio/select/role-
  select/user-select fields. OpenClaw adds its trigger button. Callback results
  return as inbound messages; preserve authorization checks on the resulting
  action. Prefer `presentation` for a cross-channel interactive message.
- Native `poll` supports voting, including multi-select and durations. Use it
  for a group preference rather than treating a button click as a vote tally.
- Components v2 and legacy embeds do not combine; the latter are ignored.
  Ordinary Markdown remains the simplest rich-text surface. URL previews are
  normally suppressed; a single send can opt in when supported by the schema.
- A single-use selection expires its sibling buttons, including a modal
  trigger. Use `reusable: true` when multiple interactions from the same card
  are intentional, or send separate cards. A private test verified both a
  string-select callback and a standalone modal submission reached the bot.
- Attach `media`/`filename` for file blocks using `attachment://<filename>`;
  text alone does not upload the file.

Canonical payload shapes: installed
`docs/channels/discord/rich-messages.md`. Check the active `message` schema
before constructing an advanced payload.
