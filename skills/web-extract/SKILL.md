---
name: web-extract
description: "Choose and use the right generic web extraction path for a task. Use when pulling data from websites, especially when deciding between lightweight retrieval, protected-site extraction, programmable browser backends, persistent extraction sessions, site-specific structured APIs, or interactive browsing. Good triggers: Cloudflare/bot-blocked pages, 'scrape this page', 'extract structured data from this site', 'find a dependable backend', or when a domain skill needs site data but should stay backend-agnostic."
---

# Web Extract

Route web-data tasks to the lightest dependable backend. Keep domain policy, site-specific paid APIs, and workflow-specific decisions in the relevant domain skill.

## Routing rules

1. Start with the lightest viable path.
2. Escalate only when the simpler path will clearly fail or already failed.
3. Treat paid/API-credit backends as deliberate choices, not defaults.
4. Keep interactive human-visible browsing separate from server-side extraction.

## Backend selection order

### 1) Lightweight retrieval
Use built-in lightweight tools first when they are enough:
- `web_search` for discovery and quick source finding
- `browser` for simple page inspection or human-visible interaction
- direct site reads only when the page is easy and unprotected

Choose this path for:
- quick fact lookup
- finding candidate URLs
- reading public pages that do not need structured extraction

### 2) Browserless
Use Browserless as the default backend for **protected server-side extraction**.

Choose it for:
- Cloudflare or anti-bot friction
- protected pages that a normal fetch/headless browser cannot read
- extracting data from a hard page without needing a human-visible browser
- cases where `/stealth/bql` or `/unblock` fits better than a naive headless fetch

Read `references/backends.md` for credentials and positioning.

Use Browserless `/session` sparingly. It is not the default for one-off reads. Use it only when repeated same-site BQL/CDP work genuinely benefits from persisted cookies, localStorage, sessionStorage, or cache. Returned session URLs include the Browserless token and must be treated as bearer credentials.

### 3) TinyFish
Use TinyFish when you need a **remote stealth browser primitive**, especially for brittle or multi-step flows.

Choose it for:
- hard pages where a full remote browser session is useful
- CDP / Playwright-style control on a hosted browser
- cases where the higher-level agent flow is too fuzzy but the site still needs stealthy browser execution

Important nuance: do **not** assume the TinyFish Agent API is the right first surface for protected extraction. The better current fit is the TinyFish Browser API / CDP session.

Read `references/backends.md` for credentials and positioning.

### 4) Site-specific structured data APIs
Domain skills own site-specific APIs, credentials, and cost policy. This skill should only say when that class of capability might fit.

Use a structured API when:
- the task needs clean structured fields more than visual/browser fidelity
- the relevant domain skill says the credit/API tradeoff is worth it
- browser extraction is blocked, too brittle, or overkill

### 5) Interactive browser mode
Use the OpenClaw `browser` tool when the task truly needs a person-facing session:
- login
- 2FA
- CAPTCHA/manual solve
- visual confirmation
- final shopping steps

## Escalation patterns

### Protected page extraction
1. Try Browserless first, especially `/stealth/bql` or `/unblock`.
2. If you need deeper remote browser control, try TinyFish Browser API / CDP session.
3. If both fail and the user has a real browser path available, switch to interactive browser work.
4. If the site remains blocked, report the limitation plainly.

When doing repeatable operational work, prefer the bundled helpers before rewriting one-off curl/CDP glue:
- `scripts/browserless_extract.py`
- `scripts/browserless_session.py`
- `scripts/tinyfish_browser_extract.py`

## Reference files

- `references/backends.md` - backend roles, secret paths, and canonical policy

## Bundled helper scripts

- `scripts/browserless_extract.py` - normalized extraction helper for Browserless `content`, `unblock`, or `stealth-bql`
- `scripts/browserless_session.py` - opt-in Browserless persistent-session helper that stores token-bearing URLs in an explicit 0600 session file and redacts normal output
- `scripts/tinyfish_browser_extract.py` - create a TinyFish browser session, drive it over CDP, and return normalized extraction JSON
