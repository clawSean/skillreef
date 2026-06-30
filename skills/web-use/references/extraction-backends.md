# Web Use Extraction Backends

Choose the lightest dependable backend for web data. Keep domain policy,
site-specific paid APIs, and workflow-specific decisions in the relevant domain
skill.

## Backend Selection Order

### 1. Lightweight Retrieval

Use built-in lightweight tools first when they are enough:

- `web_search` for discovery and quick source finding
- `web_fetch` for a specific public URL that does not need JavaScript or login
- OpenClaw `browser` for simple page inspection or human-visible interaction

Choose this path for:

- quick fact lookup
- finding candidate URLs
- reading public pages that do not need structured extraction

### 2. Browserless

Use Browserless as the default backend for protected server-side extraction.

Choose it for:

- Cloudflare or anti-bot friction
- protected pages that a normal fetch/headless browser cannot read
- extracting data from a hard page without needing a human-visible browser
- cases where `/stealth/bql` or `/unblock` fits better than a naive headless fetch

Use Browserless `/session` sparingly. It is not the default for one-off reads.
Use it only when repeated same-site BQL/CDP work genuinely benefits from
persisted cookies, localStorage, sessionStorage, or cache. Returned session URLs
include the Browserless token and must be treated as bearer credentials.

### 3. TinyFish

Use TinyFish when you need a remote stealth browser primitive, especially for
brittle or multi-step flows.

Choose it for:

- hard pages where a full remote browser session is useful
- CDP / Playwright-style control on a hosted browser
- cases where the higher-level agent flow is too fuzzy but the site still needs
  stealthy browser execution

Important nuance: do not assume the TinyFish Agent API is the right first
surface for protected extraction. The better current fit is the TinyFish Browser
API / CDP session.

### 4. Site-Specific Structured Data APIs

Domain skills own site-specific APIs, credentials, and cost policy. This skill
should only say when that class of capability might fit.

Use a structured API when:

- the task needs clean structured fields more than visual/browser fidelity
- the relevant domain skill says the credit/API tradeoff is worth it
- browser extraction is blocked, too brittle, or overkill

### 5. Interactive Browser Mode

Use the OpenClaw `browser` tool when the task truly needs a person-facing
session:

- login
- 2FA
- CAPTCHA/manual solve
- visual confirmation
- final shopping steps

## Protected Page Escalation

1. Try Browserless first, especially `/stealth/bql` or `/unblock`.
2. If you need deeper remote browser automation, try TinyFish Browser API / CDP
   session.
3. If both fail and the user has a real browser path available, switch to
   interactive browser work.
4. If the site remains blocked, report the limitation plainly.

When doing repeatable operational work, prefer the bundled helpers before
rewriting one-off curl/CDP glue:

- `../scripts/browserless_extract.py`
- `../scripts/browserless_session.py`
- `../scripts/tinyfish_browser_extract.py`

## Secret Safety

Fetch secrets at runtime. Never hardcode credentials in skill files, examples
that get committed, logs, or chat replies.

Browserless `/session` responses contain token-bearing `connect`, `browserQL`,
and `stop` URLs. Treat them like bearer credentials:

- store them only in explicit local session files
- keep session files at `0600`
- redact normal output
- stop the remote session when finished

TinyFish `cdp_url` and `base_url` can also be live browser handles. Do
not print raw values in ordinary chat output.
