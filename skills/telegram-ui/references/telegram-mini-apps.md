# Telegram Mini Apps / Games (early scaffold)

Skill-side knowledge for launching Telegram Mini Apps (web-app games and tools) from OpenClaw sends. We're early here — this holds only what's proven and Telegram-UI-shaped. The game apps themselves (server, rooms, Caddy, game design, learnings) live in the project: `~/projects/openclaw-game-night/` (STATUS/DECISIONS/LOG + `docs/telegram-webapp-2026-07-09.md`, `docs/telegram-game-ux.md`, `docs/live-game-learnings.md`).

## Proven (2026-07-09, Claw Four)

- **Mini Apps launch from groups.** The working group surface is a normal presentation `url` button pointing at the BotFather Mini App direct link — it opens natively as the Mini App and the keyboard always renders.
- True `webApp` buttons render in DMs (verified 2026-07-04). **Groups are a hard no (verified 2026-07-10, Das Groupies):** Telegram rejects the entire send with `400 BUTTON_TYPE_INVALID` — the webApp button kind is illegal in group keyboards at the API level, not merely hidden. Never mix a `webApp` button into a group send; it kills the whole message. Full launch hierarchy + payloads: SKILL.md Action Rules and `payload-recipes.md` → Group Mini App launch.

## Direct-link anatomy

`https://t.me/<bot_username>/<app_short_name>?startapp=<payload>`

- `<app_short_name>` comes from BotFather `/newapp` on the owning bot.
- `startapp` payload reaches the app (e.g. room/session id) — use it to route groups to separate rooms; one codebase, separate room state per group.

## Ownership split

- **Sean side:** web app, game server, Caddy/hosting, send/launch cards.
- **Bot-owner side (JPop):** BotFather Mini App settings (`/newapp`, URL, short name, menu button). Never ask for Telegram credentials or bot tokens for this.
- Any Caddy block/reload, gateway restart, or BotFather mutation needs JPop approval first.

## Launch-card rules (JPop preference, recorded 2026-07-09)

- Game starts are rich launch cards with a tap button — never a bare pasted URL.
- Groups/topics: primary = Mini App direct-link URL button, secondary = browser URL fallback; bare links are fallback/debug only.
- DMs/proven surfaces: true `webApp` button preferred.

## Roadmap / open

- Telegram identity inside the app (initData validation) — v2, via BotFather Mini App context.
- Which surfaces render true `webApp` buttons — DMs yes; groups closed (API-rejected, 2026-07-10). Log other surface types (channels, forum topics via DM bots) as tested.
- More games + shared patterns → track in the project, graduate stable Telegram-UI learnings back to this file.
