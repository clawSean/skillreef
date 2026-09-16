---
name: "web-use"
description: "Route web tasks across search/fetch, managed browsing, Arc/Dia fallbacks, protected extraction, authenticated sessions, and visible handoff."
---

# Web Use

Use this as the default router for web tasks. Decide two things separately:

1. **Data path:** how should the page or site data be retrieved?
2. **Browser context:** which profile, login state, visible app, or human handoff matters?

Do not pick a browser merely because one is installed or running.

## Quick route

| Need | Start with |
|---|---|
| Search or discover sources | `web_search` |
| Read a simple public URL | `web_fetch` |
| Render, inspect, or interact with a page unattended | OpenClaw managed browser |
| Managed browser is bot-blocked or lacks a needed capability | Try Arc or Dia with live page/control proof; use protected extraction for extraction-only blocks |
| Extract a protected or bot-gated page without human login | `references/extraction-backends.md` |
| Use an existing login, current tab, 2FA, CAPTCHA, extension, cart, or checkout | `references/context-device.md` |
| Apply site-specific policy or paid structured data | Relevant domain skill |

Use the lightest dependable route. Search or fetch beats browser automation when
it can finish the task. A local browser beats a paid remote backend when it can
finish safely and reliably.

## Tool-guidance loading

`web-use` owns the route. Load implementation guidance only after choosing it:

| Chosen lane | Load next |
|---|---|
| Search or fetch | The matching tool; no browser skill |
| Managed browser or shared current tab | `browser-automation` for multi-step page control |
| Existing login, profile, or human takeover | `references/context-device.md` |
| Shared-tab setup, pairing, status diagnosis, or release proof | `references/shared-tab-extension.md` |
| Protected extraction | `references/extraction-backends.md` |
| Site-specific workflow | The relevant domain skill |

`browser-automation` owns page-control mechanics after this skill chooses a
browser lane. It never chooses the data path or silently replaces search,
fetch, an API, or the user-requested browser context.

When the user explicitly asks to use, inspect, or control **their shared tab or
current browser**, pin that lane. Verify the attachment, then operate only that
shared context. Do not detour into research, a managed profile, another browser,
or extension maintenance unless the requested context is unavailable or broken.

## Browser contract

Use the managed browser for ordinary unattended interaction. Treat a visible
desktop browser as a separate, consent-bound context: an open app is not an
attached or controllable page. The shared-tab extension exposes only explicitly
shared tabs, and every run must verify the live attachment before acting.

Read `references/browser-capability-audit.md` before changing browser routing,
configuring an attachment, or making a capability claim.

## Browser naming

Keep implementation names out of user-facing instructions. Driver, engine, and
transport labels such as `cdp`, `chrome-mcp`, `Chromium`, or an executable
path describe plumbing, not the browser the user should open.

Use these labels with the user:

- **Managed browser** — isolated agent-controlled profile.
- **Your current browser** — an existing signed-in tab/session, only when
  attachment is actually verified.
- **Visible handoff** — the user must review, solve, approve, or take over.

Mention a named app only when that app has been live-inspected and is genuinely
the intended user-visible context.

## Routing rules

1. Start with the lightest viable path.
2. Escalate only when the simpler path will fail or already failed.
3. Verify the exact profile, login, visibility boundary, and attachment state.
4. Treat paid or credit-consuming backends as deliberate choices.
5. Keep interactive human-visible browsing separate from server-side extraction.
6. Keep site-specific policy in the relevant domain skill.
7. Never infer current capability from a historical VPS, node, Arc, or extension
   proof.
8. Never bypass CAPTCHA, 2FA, passkeys, confirmation gates, or irreversible
   action review.
9. When the managed browser is blocked, Arc or Dia may be tried if a visible
   local context could help; prove capture and control live before relying on it.

## Data path

### 1. Search or fetch

- `web_search` for discovery, current facts, links, and source finding.
- `web_fetch` for a known public URL that does not need JavaScript or login.
- Managed browser when rendering or interaction matters.

### 2. Managed browser

Use for ordinary rendered pages, deterministic interaction, isolated login
state, screenshots, uploads from approved roots, downloads, and unattended
multi-step work.

Before account work:

1. inspect the live page;
2. verify the account and login state;
3. verify that the managed profile is acceptable for the task;
4. stop before purchase, send, publish, delete, or other approval-gated actions.

If a dialog or browser action hangs, stop the run cleanly and report the gap.
Detection alone is not proof that the action completed.

### 3. Protected extraction

Use Browserless when the core problem is protected server-side extraction:

- Cloudflare or anti-bot friction;
- a hard page that fetch or the local managed browser cannot read;
- structured extraction without a human-visible browser.

Use Browserless sessions only when repeated same-site work genuinely needs
cookies, localStorage, sessionStorage, or cache to persist. Session URLs are
bearer credentials.

Use TinyFish when deeper hosted stealth-browser control is needed. The browser
API / remote session is the preferred primitive; do not assume its higher-level
agent API is the best route.

### 4. Site-specific APIs

Use a structured API only when the relevant domain skill owns the credential and
says the fields, reliability, and cost are worth it.

## Browser context

Use context routing for:

- an existing logged-in tab or account;
- extension state;
- CAPTCHA, 2FA, passkeys, or manual review;
- cart, checkout, order history, account settings, or irreversible actions;
- a user-visible page where the human must take over.

Preferred plain-English modes:

- Fresh managed browser
- Your current browser
- Visible handoff

Read `references/context-device.md` for availability and consent rules.

## Escalation patterns

### Public page

1. Search if the source is unknown.
2. Fetch if the URL is known and likely static.
3. Use the managed browser if rendering or interaction matters.

### Protected page

1. Try the managed browser if ordinary rendering may be enough.
2. If it is bot-blocked or lacks a needed capability and a visible local context
   may help, try Arc or Dia as a fallback experiment. Live-prove the exact page
   capture and control path before relying on it.
3. Use Browserless `/unblock` or `/stealth/bql` for extraction-only blocks.
4. Use a Browserless session only for demonstrated persistence needs.
5. Use TinyFish for deeper hosted browser control.
6. Use verified manual handoff for CAPTCHA/2FA, passkeys, provider approval, or
   review that must remain human-controlled.
7. Report blockage plainly if the site still resists.

### Existing login or current tab

1. Confirm that existing session state is actually required.
2. Check whether the managed profile is already signed in and acceptable.
3. If the user's current tab is required, verify a live supported attachment.
4. If no attachment is live, say so and offer the managed-browser or manual
   handoff path.
5. Do not treat a running Arc or Dia process as attached.
6. Do not instruct the user to configure an implementation browser unless that
   named browser is truly required and the setup is approved.

## Bundled helpers

- `scripts/browserless_extract.py` — Browserless content, unblock, or stealth BQL
- `scripts/browserless_session.py` — opt-in persistent Browserless session with
  redacted output and `0600` session files
- `scripts/tinyfish_browser_extract.py` — TinyFish browser-session extraction

See `references/backends.md.example` for public-safe setup patterns.

## References

- `references/browser-capability-audit.md` — current ClawPop proof, gaps, and
  browser evaluation
- `references/context-device.md` — context, consent, and attachment matrix
- `references/shared-tab-extension.md` — rare setup, pairing, diagnosis, and
  release-proof branch for the shared-tab extension
- `references/extraction-backends.md` — backend ladder and safety notes
- `references/backends.md` — Sean-local backend operating notes
- `references/backends.md.example` — public-safe configuration template
