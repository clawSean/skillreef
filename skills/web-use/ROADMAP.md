# ROADMAP - web-use

## Browser Automation Consolidation

- [x] Consolidate browser-control routing, tab hygiene, stale ref recovery, and
  login/manual-blocker guidance into `SKILL.md`.
- [x] Keep `web-use` as the single model-visible local source of truth for
  web/browser work.
- [x] Remove the local `plugin-skills/browser-automation` symlink instead of
  keeping a shim or duplicate skill entry.
- When OpenClaw's bundled native `browser-automation` skill changes upstream,
  compare it as reference material and fold useful updates into `web-use`
  instead of re-adding a companion skill.
- Add a smoke test playbook for a harmless page navigation and screenshot/check
  flow.
