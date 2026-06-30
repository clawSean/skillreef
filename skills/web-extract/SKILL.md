---
name: web-extract
description: "Compatibility alias for extraction-backend routing now owned by web-use. Prefer web-use; use this only when specifically asked about lightweight retrieval vs Browserless, TinyFish, persistent remote sessions, site-specific APIs, or interactive browser escalation for protected/bot-gated page data."
---

# Web Extract

Canonical web routing now lives in `web-use`.

Use `web-use` for full web routing, including backend selection. Extraction
details live in `web-use/references/extraction-backends.md`; credential and
command templates live in `web-use/references/backends.md.example`.

This alias is retained for callers that still name `web-extract` directly.
