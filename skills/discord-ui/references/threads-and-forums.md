# Threads and forums

- In a text channel, `message(action="thread-create", channelId=<parent>,
  threadName=<title>, message=<opening>)` creates a public thread and can post
  its opening. Confirm `initialMessageDelivery.status` and message IDs; the
  creation snapshot's `message_count: 0` does not mean delivery failed.
- Reply with `thread-reply` and `threadId`, or `send` to
  `target="channel:<threadId>"`. Read with `channelId=<threadId>`. `thread-list`
  requires `guildId` and may include `channelId=<parent>`.
- For forum/media parents, send to the parent to auto-create a post (the first
  nonempty line becomes its title), or explicitly create a thread. Do not pass
  a message ID to forum thread creation. Send Components v2 to the created
  thread, not the forum parent.
- Threads have separate channel sessions. They inherit the parent's Discord
  allowlist/config, but not necessarily its transcript; verify whether the bot
  needs a mention for follow-ups. Do not promise seamless unmentioned follow-ups
  solely because the bot created the thread.
- Private threads require a distinct permission and audience choice. Check
  `CreatePrivateThreads`; don't move private content into a public thread.
- Partial initial-delivery failures may be ambiguous. Read the thread before
  retrying. Archive/lock/rename operations need their own tool and permission
  checks; creating a thread does not imply managing other people's threads.

Runtime details: installed `docs/channels/discord/threads-and-sessions.md` and
`access-control.md`.
