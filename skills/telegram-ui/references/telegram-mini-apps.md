# Telegram Mini Apps

Use this branch only after `SKILL.md` selects a Mini App interaction. Current
typed payloads live in `payload-recipes.md`; keep project hosting, game logic,
and room state in the owning project rather than this UI skill.

## Group API evidence

On 2026-07-10, a true `web-app` action in a group keyboard caused Telegram to
reject the whole send with `400 BUTTON_TYPE_INVALID`. A normal `url` action to
the BotFather direct link rendered and launched the Mini App. `SKILL.md` owns
the resulting surface decision; `payload-recipes.md` owns the payload shapes.

## Direct-link anatomy

`https://t.me/<bot_username>/<app_short_name>?startapp=<payload>`

- `<app_short_name>` comes from BotFather `/newapp` on the owning bot.
- `startapp` carries a compact app-owned route such as a room/session ID. Do not
  put secrets or credentials in it.

## Verify

1. Confirm the send returns a real message ID and the expected keyboard appears.
2. Open the button in the actual Telegram client and verify the intended app and
   route load. A successful send alone does not prove the launch target works.
3. Keep BotFather and hosting mutations outside this send-time branch; they need
   their own explicit scope and approval. Never request bot credentials or tokens.
