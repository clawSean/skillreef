# Discord capability map

The `message` tool currently exposes these Discord action families. Check
the active schema and `channels.discord.actions.*` before use; defaults may
change and account/channel permissions are separate.

- Conversation: send, read, search, reply, edit, delete/unsend, reactions and
  reaction listing, pins, native polls, attachments, stickers.
- Topics: thread-create, thread-reply, thread-list, forum/media posts, thread
  binding/session routing.
- Server: channel-list/info/create/edit/move/delete, categories, member/role
  info, events, emoji list/upload, sticker upload, permissions, voice status,
  presence, moderation. Administration is not a routine conversation action.
- Rich: native Markdown, Components v2 buttons/selects/modals/galleries/files,
  cross-channel presentation, optional link previews, voice/media surfaces.
  Discord Activities can launch HTML widgets, but require separate opt-in
  config, a client secret, public HTTPS, and Developer Portal setup.

## Local observations — 2026-11-25

- In one private test server, thread creation/opening delivery, Markdown
  send/readback, a Components v2 button card, and a native poll all worked.
  The rendered card and poll were also inspected in a signed-in Discord client;
  button callbacks were not tested.
- A second private test server granted the bot `ManageThreads` and
  `PinMessages`. Effective permissions readback showed both, and renaming a
  bot-created thread succeeded. `ManageChannels` was not granted.
- Pin, list-pins, and unpin succeeded in the originating conversation. The
  delegated `pin` and `react` actions rejected cross-thread targets because
  they require the exact current conversation/account. This is a tool-scope
  boundary, not evidence that Discord denied those permissions.
- `channels.discord.activities` is unset, so Activity widgets are not active.
  Do not describe them as live or modify runtime config as part of UI usage.
- `channels.discord.actions` is unset; installed docs say conversation action
  groups default enabled, while roles/moderation/presence default disabled.

For fresh status, call `message(action="permissions", channelId=<target>)` and
read the installed Discord docs. Do not extrapolate this dated proof to other
guilds or future OpenClaw generations.
