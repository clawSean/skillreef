---
name: browser-control
description: "Compatibility alias for browser-context routing now owned by web-use. Prefer web-use; use this only when specifically asked about fresh vs existing browser, user vs agent device, visible/headless mode, current tab, logged-in browser, extension lane, CAPTCHA/2FA, cart, or checkout context."
---

# Browser Control

Canonical web routing now lives in `web-use`.

Use `web-use` for full web routing, including browser context. Browser context
details live in `web-use/references/context-device.md`.

This alias is retained for callers that still name `browser-control` directly.
