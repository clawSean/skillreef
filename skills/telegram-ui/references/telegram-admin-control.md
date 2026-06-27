# Telegram Admin / Control Actions

Use this reference for rare Telegram group-level control actions that sit near UI/media work but are not ordinary message rendering.

Examples:
- Change a group/supergroup profile photo.
- Check whether the bot has admin capabilities in a chat.
- Call Telegram Bot API methods that OpenClaw's `message` tool does not expose directly.

These actions mutate group state. Only do them when the user explicitly asks, or when the requested workflow clearly requires it.

## Change Group Profile Photo

Telegram Bot API method: `setChatPhoto`.

### Requirements

- The bot must be a group admin.
- The bot needs `can_change_info: true` for the target group/supergroup.
- The target image should already be finalized and available as a local file.
- Prefer square images for group avatars. Remember Telegram clients often display them through a circular mask.

### Permission Check

```bash
CHAT='<telegram_chat_id>'
TOKEN='<telegram_bot_token>'
BOT_ID=$(curl -fsS "https://api.telegram.org/bot${TOKEN}/getMe" | jq -r '.result.id')

curl -fsS --get "https://api.telegram.org/bot${TOKEN}/getChatMember" \
  --data-urlencode "chat_id=${CHAT}" \
  --data-urlencode "user_id=${BOT_ID}" \
  | jq '{ok, status: .result.status, can_change_info: .result.can_change_info, can_manage_chat: .result.can_manage_chat}'
```

Proceed only if Telegram returns `status: "administrator"` or equivalent owner/admin status and `can_change_info: true`.

### Set The Photo

```bash
CHAT='<telegram_chat_id>'
PHOTO='/absolute/path/to/avatar.png'
TOKEN='<telegram_bot_token>'

curl -fsS -X POST "https://api.telegram.org/bot${TOKEN}/setChatPhoto" \
  -F "chat_id=${CHAT}" \
  -F "photo=@${PHOTO}" \
  | jq
```

Expected success:

```json
{
  "ok": true,
  "result": true
}
```

### Verify

```bash
curl -fsS --get "https://api.telegram.org/bot${TOKEN}/getChat" \
  --data-urlencode "chat_id=${CHAT}" \
  | jq '{ok, title: .result.title, photo: .result.photo}'
```

A fresh `photo.small_file_id` / `photo.big_file_id` confirms Telegram accepted the update.

## Notes

- Do not print or expose bot tokens.
- Do not restart OpenClaw or Telegram services for this.
- If permission is missing, tell the user the bot needs to be promoted with group-info/photo permission.
- For ordinary image delivery, use the `message` tool with `media=...`; `setChatPhoto` is only for changing the chat profile image.
