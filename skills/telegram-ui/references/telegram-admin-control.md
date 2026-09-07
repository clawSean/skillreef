# Telegram Admin and Group Controls

Use only for an explicitly requested Telegram group mutation that ordinary
message delivery does not cover, such as changing group info or its image.

## Safety contract

1. Resolve the exact chat and Telegram account from trusted runtime context.
2. Inspect the active `message` tool schema and account action gates.
3. Use a supported native `message` action when exposed.
4. Verify the returned chat/message state and inspect the Telegram client.
5. If the native action or required field is absent, stop and report that exact
   runtime gap. Do not construct a raw Bot API command from model context.

Never request, read, echo, interpolate, log, or place a bot token in chat,
commands, URLs, shell variables, or durable files. A successful send does not
prove the requested admin mutation occurred.

## Change a group image

Preconditions:

- the user explicitly approved the named group and final image;
- the chat ID and selected bot account are verified;
- the bot has permission to change group information;
- the active `message` schema exposes its group-icon action;
- the finalized local image is square and crop-safe.

Use the current tool's declared field names rather than copying a stale payload.
After the action returns, inspect the group header/avatar in Telegram. If the
permission is missing, report the exact administrator permission needed. Never
retry a mutating admin action blindly after an ambiguous result.

## Other group mutations

Renaming, membership changes, and leaving a group follow the same contract:
explicit scope, current native action, permission proof, one mutation, and
readback. Do not infer authorization for a different group-level change from a
message-formatting request.

Forum-topic mutations use `telegram-forum-topics.md` instead.
