---
name: web-use
description: "Use for any task that touches a web page or web data. Routes between web_search/web_fetch, Browserless/TinyFish/protected extraction, OpenClaw browser, and live browser context for login, 2FA, CAPTCHA, current tabs, carts, or checkout. Prefer this front door before browser-control or web-extract; domain skills keep site-specific policy."
---

# Web Use

Use this as the default routing layer for web work. Decide the lightest
dependable path before reaching for a browser or protected extraction backend.

This skill answers two separate questions:

1. **Data path:** how should the page or site data be retrieved?
2. **Browser context:** whose browser, device, tab, or login state matters?

Keep those questions separate even when one workflow needs both.

## Quick Route

| Need | Start with |
|---|---|
| Search, discovery, quick source finding | `web_search` |
| Read a simple public URL | `web_fetch` |
| Inspect a JS-rendered page visually | OpenClaw `browser` |
| Extract protected or bot-gated data | `references/extraction-backends.md` |
| Use a current tab, login, 2FA, CAPTCHA, extension, cart, or checkout | `references/context-device.md` |
| Site-specific paid API or domain policy | Relevant domain skill |

Do not use a browser when search or fetch is enough. Do not use Browserless,
TinyFish, or paid APIs when a simple tool can finish the task.

## Routing Rules

1. Start with the lightest viable path.
2. Escalate only when the simpler path will clearly fail or already failed.
3. Treat paid/API-credit backends as deliberate choices, not defaults.
4. Keep interactive human-visible browsing separate from server-side extraction.
5. Keep site-specific policy in the relevant domain skill.

## Data Path Decision

### 1. Lightweight Search Or Fetch

Use native OpenClaw tools first when they are enough:

- `web_search` for discovery, source finding, current facts, and links.
- `web_fetch` for a specific public URL that does not need JavaScript or login.
- OpenClaw `browser` for simple visual inspection when rendering matters.

### 2. Protected Server-Side Extraction

Use Browserless when the core problem is getting through protection and
extracting page data without a human-visible browser:

- Cloudflare or anti-bot friction
- protected pages that a normal fetch or local headless browser cannot read
- structured extraction from a hard page

Use Browserless `/session` sparingly. It is not the default for one-off reads.
Use it only when repeated same-site BQL/CDP work genuinely benefits from
persisted cookies, localStorage, sessionStorage, or cache. Session URLs include
the Browserless token and act as bearer credentials.

### 3. Remote Stealth Browser Primitive

Use TinyFish when you need a hosted stealth browser you can control:

- brittle multi-step flows
- custom CDP / Playwright-style control
- hard pages where a remote browser session is useful

Do not assume the TinyFish Agent API is the first surface for protected
extraction. The better current fit is the TinyFish Browser API / CDP session.

### 4. Site-Specific Structured APIs

Use a structured API only when the relevant domain skill says the clean fields,
cost, and credential policy are worth it. Keep API-specific policy out of this
skill.

## Browser Context Decision

Use browser context routing when the task needs one of these:

- deciding between fresh browser vs current browser
- deciding between user device vs agent device
- preserving or using an existing logged-in tab/session
- a visible browser on the user's device
- a browser extension lane
- CAPTCHA, 2FA, manual review, cart, checkout, or account state
- user-facing UX/design for browser intents

Plain-English labels:

- Fresh browser
- Your current browser
- On your device
- On my side

Read `references/context-device.md` for the compact 2 x 2 browser-mode matrix
and phrasing guide.

## Escalation Patterns

### Public Page

1. `web_search` if the URL/source is unknown.
2. `web_fetch` if the URL is known and likely static.
3. OpenClaw `browser` if JavaScript/rendering matters.

### Protected Page Data

1. Try Browserless `/stealth/bql` or `/unblock`.
2. Use Browserless `/session` only for repeated same-site work that benefits
   from persisted remote state.
3. Use TinyFish Browser API / CDP when deeper remote browser control is needed.
4. Use a site-specific API only when the domain skill approves the tradeoff.
5. Switch to interactive browser work when login, CAPTCHA/2FA, visible review,
   or extension state matters.
6. If the site remains blocked, say so plainly.

### Current Tab Or Logged-In Browser

1. Confirm that the task needs the user's live browser/session.
2. Use the available browser profile/node path for the target device.
3. If the requested mode is unavailable, say which capability is missing and
   choose the closest acceptable fallback.

## Bundled Helper Scripts

Use these from this skill directory when repeatable execution helps:

- `scripts/browserless_extract.py` - Browserless `content`, `unblock`, or `stealth-bql`
- `scripts/browserless_session.py` - opt-in persistent Browserless session helper with redacted output and 0600 session files
- `scripts/tinyfish_browser_extract.py` - TinyFish Browser API / CDP extraction helper

See `references/backends.md.example` for credential and command templates.

## Reference Files

- `references/context-device.md` - browser context/device/session matrix
- `references/extraction-backends.md` - backend ladder and safety notes
- `references/backends.md.example` - public-safe credential and command template
