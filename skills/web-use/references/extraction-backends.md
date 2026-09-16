# Web Use Extraction Backends

Choose the lightest dependable backend for web data. Keep site policy, paid API
decisions, and credentials in the relevant domain skill.

## Selection order

### 1. Lightweight retrieval

- `web_search` for discovery and source finding
- `web_fetch` for public URLs that do not need JavaScript or login
- managed browser for ordinary rendering and interaction

The managed browser is agent-side and currently headless. Do not describe it as
automatically person-facing.

Before using a remote extraction backend, distinguish a data-path block from a
browser-context block. If a visible local profile, login, or app-specific path
may help, try Arc or Dia under the live-proof rules in `../SKILL.md`.
Browserless and TinyFish remain extraction-only alternatives unless the owning
domain policy and the user explicitly authorize transferring authenticated
session state.

### 2. Browserless

Use Browserless for protected server-side extraction:

- Cloudflare or anti-bot friction;
- a hard page that fetch or local managed browsing cannot read;
- structured extraction without a human-visible browser.

Prefer stateless `/unblock` or `/stealth/bql` calls. Use `/session` only
when repeated same-site work demonstrably needs cookies, localStorage,
sessionStorage, or cache to persist. Session URLs contain bearer credentials.

### 3. TinyFish

Use TinyFish when a hosted stealth-browser session needs deeper multi-step
control. Prefer the browser API / remote session. Do not assume the higher-level
agent API is the best protected-extraction surface.

### 4. Site-specific APIs

Use a structured API only when the domain skill owns the credential and approves
the reliability, field quality, and cost tradeoff.

### 5. Verified visible handoff

Switch to visible handoff when login, 2FA, CAPTCHA, passkeys, manual review, or
final approval matters. A visible app being installed or running is not proof of
page-level agent control.

## Protected-page escalation

1. Try the managed browser for ordinary rendering.
2. If a signed-in or visible local context may help, try Arc or Dia and
   live-prove the exact page capture/control path.
3. Use Browserless `/unblock` or `/stealth/bql` for extraction-only blocks.
4. Use a Browserless session only for proven persistence needs.
5. Use TinyFish for deeper hosted browser control.
6. Use a verified manual handoff for user-only gates.
7. Report blockage plainly.

## Secret safety

Fetch credentials only at runtime through the owning secret workflow. Never
hardcode them in skills, committed examples, logs, or chat.

Treat Browserless session URLs and TinyFish remote-session URLs as bearer
credentials. Redact them, keep local session files at `0600`, and close remote
sessions when finished.

Do not export authenticated cookies, localStorage, sessionStorage, or other
signed-in state from the managed browser, Arc, or Dia to Browserless or TinyFish
without explicit user authorization and an owning domain policy that permits it.

## Helpers

- `../scripts/browserless_extract.py`
- `../scripts/browserless_session.py`
- `../scripts/tinyfish_browser_extract.py`
