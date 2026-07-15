# Telegram Forum Topics (Create / Edit / Post Into)

Managing topics in forum-enabled supergroups. Fully native — the OpenClaw `message` tool exposes Telegram's `createForumTopic` / `editForumTopic`, no raw Bot API calls needed.

Verified working 2026-07-09 in Das Groupies (`-1003778833824`): created topic 5054, posted into it, confirmed in General.

## Requirements

- The group must be a **forum** (topics enabled) supergroup.
- The bot must be an admin with the **Manage Topics** permission. Without it, topic-create fails with `400: not enough rights to create a topic` — ask the owner to toggle it on under Group settings → Administrators → bot → Manage Topics.

## Create a Topic

```json
{
  "action": "topic-create",
  "name": "🦞 New Topic Name"
}
```

- `target` defaults to the current chat; pass `target: "<chat_id>"` to create in another group.
- Returns `{ ok, topicId, name, chatId }` — capture `topicId` for follow-up sends.
- Emoji in topic names works fine.

## Post Into a Topic

Use `threadId` with the topic id:

```json
{
  "action": "send",
  "target": "-1003778833824",
  "threadId": "5054",
  "message": "<p>Hello from inside the topic 🦞</p>"
}
```

Same pattern works for other actions (polls, media, etc.) — `threadId` routes them into the topic. Omitting `threadId` posts to General (topic 1).

## Rename / Edit a Topic

```json
{
  "action": "topic-edit",
  "threadId": "5054",
  "name": "🦞 Renamed Topic"
}
```

## Notes

- Topic ids are message-thread ids; inbound context exposes the current one as `topic_id`.
- Session keys are per-topic (`...:topic:<id>`), so each topic is its own conversation lane — useful for per-project or per-person threads.
- Deletion isn't wired here; leave that to humans in the Telegram UI.
