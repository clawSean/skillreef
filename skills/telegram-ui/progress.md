# Telegram Buttons — Local Progress Notes

This file is intentionally git-ignored. Use it for transient implementation notes while improving Telegram button behavior.

## 2026-05-01 — Plugin command button research

Research note created:

- `skills/plugin-creator/references/telegram-command-buttons.md`

Key takeaway: `/think`-style `argsMenu: "auto"` is the cleanest native-command pattern, but current public plugin command types may not expose `argsMenu`. For plugin-owned two-branch choices, use raw slash args or `presentation.buttons` + `api.registerInteractiveHandler(...)`; reserve `/models`-style custom pickers for stateful, multi-step, paginated, or message-editing flows.

Related one-shot prompt/template:

- `skills/plugin-creator/references/one-shot-extension-prompt.md`

## 2026-07-09 — Restructure + parked TODOs

SKILL.md restructured (dedup mandates → Pre-Send Checklist + House Rules; matrix detail → references/rich-rendering-matrix.md; toolchest kept fully enumerated per JPop).

Parked TODOs (moved out of SKILL.md):
- ⏳ Re-verify group final-delivery regression (#76424) post-richMessages rollout, plus media gotchas + voice-message limitation.
- 🧪 scripts/test.sh reports "4 of 17 JSON blocks invalid" — pre-existing (fails on the pre-restructure file too); likely ellipsis placeholders in examples. Decide: fix examples or teach the test to skip placeholder blocks.
