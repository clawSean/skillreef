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
default. The Telegram adapter supports `iconCustomEmojiId`, but the observed
2026.9.7 model-facing `message` schema does not expose it. Recheck the active
schema before each icon operation; do not confuse a schema gap with a Telegram
or adapter limitation.

Use the icon only when the active schema exposes the field and the ID came from
Telegram's allowed forum-topic icon set. Never invent or recycle a sticker or
inline custom-emoji ID. If the field is unavailable, create the requested topic
only when the user accepts the default-icon limitation, and report it clearly.
Direct Bot API use is not the default; it needs explicit authorization for that
operation and secret-safe handling.

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

### Temporary authority fallback (observed 2026-10-07)

The intended route is the agent `message` action above. On OpenClaw 2026.9.7,
fresh Telegram turns returned `Gateway client authority closed before
dispatching message.action` even for read-only `message` calls. This is an
in-turn caller-authority failure, **not** evidence that Telegram rejected the
name, emoji, bot permission, or the reviewer's `operator.admin` grant. Do not keep
retrying the same action or change Gateway config to guess at a fix.

If that exact failure recurs, the authenticated `openclaw gateway call
message.action` CLI can reach the usual OpenClaw Telegram adapter with a fresh
client. This is a **workaround, not the intended agent-tool route**; its RPC
shape and the bridge bug may change. Recheck the active Gateway schema and
prefer the agent tool again once it passes. For the observed version, use a
unique idempotency key, explicit account and chat, and provider-specific
`chatId`; direct Gateway calls using `target` or `to` instead failed with
`ToolInputError: to required`.

```sh
openclaw gateway call message.action --json --params '{"idempotencyKey":"<unique-per-edit>","action":"topic-edit","channel":"telegram","params":{"accountId":"<account>","chatId":"<verified-chat-id>","threadId":"<topic-id>","name":"<new-name>"}}'
```

Treat Telegram `TOPIC_NOT_MODIFIED` as confirmation that the requested name is
already set, **not** as a successful edit receipt. If the Gateway route cannot
work, use direct Bot API only with explicit authorization for that operation;
never put the bot token in a command argument, log, or response. Record which
route actually changed the topic. Dated repro/evidence:
`knowledge/research/telegram-topic-tool-authority-2026-10-07.md`.

## Boundaries

- Topic IDs are message-thread IDs; inbound context exposes the current one.
- Sessions are topic-scoped, so each topic has its own conversation lane.
- Telegram supports true close/reopen only for forum supergroups, not private
  chats with topics. Private-topic deletion also deletes its messages; never
  present that destructive operation as ordinary close/archive.
- If the active `message` schema exposes `topic-close` or `topic-reopen`, use it.
  Otherwise the bundled helper provides a token-safe local lane without a
  Gateway config change:

```bash
node scripts/topic-lifecycle.mjs inspect --chat '<supergroup-id>' --account '<account>'
node scripts/topic-lifecycle.mjs close --chat '<supergroup-id>' --thread '<topic-id>' --account '<account>'
node scripts/topic-lifecycle.mjs reopen --chat '<supergroup-id>' --thread '<topic-id>' --account '<account>'
```

  Run it from this skill directory. It loads the selected account through
  OpenClaw's runtime config and token resolver, validates the forum and Manage
  Topics permission, redacts Telegram failures, and never prints the token.
  `thread=1` uses Telegram's dedicated General-topic method. Capture the JSON
  receipt. Do not retry an ambiguous mutation.
- Topic deletion is not exposed here. Leave it to a human unless a future
  reviewed native action adds an explicit destructive-operation contract.
