# Telegram Forum Topics

Use for creating, editing, or posting into a forum-enabled Telegram supergroup.
These are external group mutations; require explicit scope and verify the bot's
Manage Topics permission.

## Create

```json
{
  "action": "topic-create",
  "name": "🦞 New Topic Name"
}
```

`target` defaults to the current chat. Pass a verified target only for another
group. Capture the returned `topicId` and inspect the topic in Telegram.

### Native icon

The reviewer's preference is an intentional native topic icon rather than Telegram's
default. The runtime field is `iconCustomEmojiId`, but the installed 2026.9.1
model-facing message schema does not expose it.

Use the icon only when the active schema exposes the field and the ID came from
Telegram's allowed forum-topic icon set. Never invent or recycle a sticker or
inline custom-emoji ID. If the field is unavailable, create the requested topic
only when the user accepts the default-icon limitation, and report it clearly;
do not fall back to a token-bearing raw Bot API command.

## Post into a topic

```json
{
  "action": "send",
  "target": "<chat_id>",
  "threadId": "<topic_id>",
  "message": "Hello from inside the topic 🦞"
}
```

Omitting `threadId` posts to General. Polls and media use the same `threadId`
routing.

## Edit

```json
{
  "action": "topic-edit",
  "threadId": "<topic_id>",
  "name": "🦞 Renamed Topic"
}
```

Verify the returned topic ID/name and inspect the visible result. If the action
fails ambiguously, stop rather than retrying a mutation blindly.

## Boundaries

- Topic IDs are message-thread IDs; inbound context exposes the current one.
- Sessions are topic-scoped, so each topic has its own conversation lane.
- Topic deletion is not exposed here; leave it to a human unless the active tool
  explicitly adds a reviewed delete action.
