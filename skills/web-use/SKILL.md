---
name: "web-use"
description: >
  Default routing layer for all web work: pick the lightest path among
  web_search, web_fetch, OpenClaw browser control, Browserless /unblock, and
  TinyFish. Read before browsing, scraping, multi-step browser flows, or before
  declaring any page blocked; Cloudflare, CAPTCHA, and "Just a moment" pages get
  /unblock first. Covers live browser context for login, 2FA, CAPTCHA, current
  tabs, carts, and checkout.
---

# Web Use

Use this as the default routing layer for web work. Decide the lightest
dependable path before reaching for a browser or protected extraction backend.

This skill answers three separate questions:

1. **Data path:** how should the page or site data be retrieved?
2. **Browser context:** whose browser, device, tab, or login state matters?
3. **Browser control:** once the OpenClaw `browser` tool is the right path, how
   should it be driven reliably?

Keep these separate even when one workflow needs more than one.

## Consolidation Note

OpenClaw also ships a native bundled `browser-automation` skill under its
browser extension. In this workspace, do not expose that as a separate local
skill, shim, or `plugin-skills/browser-automation` symlink. The useful browser
control mechanics are consolidated here so web routing, browser context, and
browser operation have one model-visible source of truth.

OpenClaw's skills CLI may recreate `~/.openclaw/plugin-skills/browser-automation`
while enumerating extra skills, even when `skills.entries.browser-automation.enabled=false`.
Treat that symlink as generated index state, not a source of truth. The durable
state is the config disable plus this consolidation note; if the symlink
reappears, leave it disabled or remove it again instead of using it.

If the bundled skill changes upstream, compare it as reference material and
fold any useful updates into `web-use` instead of resurrecting a second local
skill entry.

## Quick Route

| Need | Start with |
|---|---|
| Search, discovery, quick source finding | `web_search` |
| Read a simple public URL | `web_fetch` |
| Inspect a JS-rendered page visually | OpenClaw `browser` |
| Drive a multi-step browser flow, login, tabs, cart, checkout, recovery | OpenClaw `browser` — see Browser Tool Control |
| Extract protected or bot-gated data | Browserless `/unblock` first, then `references/extraction-backends.md` |
| Use a current tab, login, 2FA, CAPTCHA, extension, or account state | `references/context-device.md` |
| Resolve, download, or transcribe a video or media URL | `video` skill if present, else a local resolver (yt-dlp/ffprobe) then a headless-render fallback |
| Site-specific paid API or domain policy | Relevant domain skill |

**Cloudflare / anti-bot stop rule:** a page showing "Just a moment", "Checking
your browser", "We'll have you designing again soon", CAPTCHA, Turnstile,
Access Denied, or similar bot-gate copy is not a final block. Run Browserless
`/unblock` before saying the page cannot be accessed. Only call it blocked after
`/unblock` has failed and login/current-browser escalation is not appropriate.

Do not use a browser when search or fetch is enough. Do not use Browserless,
TinyFish, or paid APIs when a simple tool can finish the task.

## Logged-In Sessions Are Not User-Device-Only

A logged-in browser session can live on the agent side, not just the user's
machine. A managed OpenClaw browser profile can hold durable logins and may be
the primary lane for cart, checkout, order-history, and account tasks. The user's
own device browser is a fallback when the agent-side session is logged out or
the user wants to co-interact.

When a task needs a logged-in session, check the agent-side managed browser
first, verify login state on the live page, then fall back to the user device if
needed. Do not assume "logged in" means "the user's current browser."

## Routing Rules

1. Start with the lightest viable path.
2. Escalate only when the simpler path will clearly fail or already failed.
3. Treat paid/API-credit backends as deliberate choices, not defaults.
4. Keep interactive human-visible browsing separate from server-side extraction.
5. Keep site-specific policy in the relevant domain skill.
6. A logged-in session may be agent-side; verify login state instead of routing
   by device assumption.

## Data Path Decision

### 1. Lightweight Search Or Fetch

Use native OpenClaw tools first when they are enough:

- `web_search` for discovery, source finding, current facts, and links.
- `web_fetch` for a specific public URL that does not need JavaScript or login.
- OpenClaw `browser` for simple visual inspection when rendering matters.

If any lightweight path lands on an anti-bot wall, immediately switch to
Browserless `/unblock`; do not treat the lightweight failure as terminal.

### 2. Protected Server-Side Extraction

Use Browserless when the core problem is getting through protection and
extracting page data without a human-visible browser:

- Cloudflare or anti-bot friction
- protected pages that a normal fetch or local headless browser cannot read
- structured extraction from a hard page

For Cloudflare, Turnstile, CAPTCHA-like holding pages, or branded anti-bot pages,
prefer Browserless `/unblock` as the first server-side extraction mode. Use
`/stealth/bql` when you specifically need programmable BQL behavior or when
`/unblock` does not expose enough useful content.

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

## Browser Tool Control

Once the OpenClaw `browser` tool is the right path and the task is anything
beyond a single page check, use this loop.

### Operating Loop

1. Check browser state before acting:
   - `openclaw browser doctor` or `action="status"` when the browser/plugin setup itself may be broken.
   - `action="status"` for availability.
   - `action="profiles"` if login state or profile choice matters.
   - `action="tabs"` before opening a new tab if retries/timeouts may have left windows behind.
2. Prefer stable tab handles:
   - Open important tabs with `label`, for example `label="meet"`.
   - After `action="tabs"` or `action="open"`, store `suggestedTargetId` and pass it as `targetId` in later calls.
   - `suggestedTargetId` is the label when one exists, otherwise the stable `tabId` handle like `t1`.
   - Avoid relying on raw DevTools `targetId` except for immediate diagnostics; it can change under Chromium target replacement.
3. Read before clicking:
   - Use `action="snapshot"` on the intended `targetId`.
   - Use the same `targetId` for follow-up actions so refs stay on the same tab.
   - For durable Playwright refs, request `refs="aria"` when supported. If you receive `axN` refs from `snapshotFormat="aria"`, use them only after that same snapshot call; stale or unbound `axN` refs fail fast and need a fresh snapshot.
   - Use `urls=true` when link text is ambiguous or a direct navigation target would avoid brittle clicks.
   - Use `labels=true` on snapshot or screenshot when visual position matters.
4. Act narrowly:
   - Prefer `action="act"` with a ref from the latest snapshot.
   - After navigation, modal changes, or form submission, snapshot again before the next action.
   - Avoid blind waits. Wait for visible UI state when possible.
5. Report real blockers:
   - If the page needs login, permission, CAPTCHA, 2FA, camera/microphone approval, or another manual step, stop and tell the user exactly what is needed.
   - Do not claim the browser is not logged in just because the current page shows a permission or onboarding dialog. Inspect the visible UI first.

### Tab Hygiene

Before creating a tab for a named task, list tabs and reuse an existing matching
label or URL when it is still usable.

```json
{ "action": "tabs" }
```

If no suitable tab exists:

```json
{ "action": "open", "url": "https://example.com", "label": "task" }
```

Then target it by label:

```json
{ "action": "snapshot", "targetId": "task", "refs": "aria" }
```

If a retry creates duplicates, close the extras by `tabId`:

```json
{ "action": "close", "targetId": "t3" }
```

Do not pass bare numbers like `"2"` as `targetId`. Numeric tab positions are only
for the CLI `openclaw browser tab select 2` helper; browser tool calls need a
`suggestedTargetId`, label, `tabId`, or raw target id.

### Stale Ref Recovery

If an action fails with a missing or stale ref:

1. Snapshot the same `targetId` again.
2. Find the current visible control.
3. Retry once with the new ref.
4. If the UI moved to a blocker state, report the blocker instead of looping.

### Existing User Browser

Use `profile="user"` only when existing cookies/login matter. This attaches to
the user's running Chromium-based browser.

For `profile="user"` and other existing-session profiles, omit `timeoutMs` on
`act:type`, `evaluate`, `hover`, `scrollIntoView`, `drag`, `select`, and `fill`;
that driver rejects per-call timeout overrides for those actions.

### Google Meet Notes

When creating or joining a Meet:

- Treat camera/microphone permission screens as progress, not login failure.
- If asked whether people can hear you, click the microphone option when voice is required.
- If Google asks for sign-in, 2FA, account chooser confirmation, or permission that needs user approval, report the exact manual action.
- Use one labeled tab per meeting flow, for example `label="meet"`, and reuse it during retries.

## Escalation Patterns

### Public Page

1. `web_search` if the URL/source is unknown.
2. `web_fetch` if the URL is known and likely static.
3. OpenClaw `browser` if JavaScript/rendering matters.
4. If any step hits Cloudflare, Turnstile, CAPTCHA-like, Access Denied, or a
   branded bot-gate page, run Browserless `/unblock` before reporting failure.

### Protected Page Data

1. Try Browserless `/unblock` first for Cloudflare/anti-bot pages.
2. Try Browserless `/stealth/bql` when BQL behavior is needed or `/unblock` does
   not expose useful content.
3. Use Browserless `/session` only for repeated same-site work that benefits
   from persisted remote state.
4. Use TinyFish Browser API / CDP when deeper remote browser automation is needed.
5. Use a site-specific API only when the domain skill approves the tradeoff.
6. Switch to interactive browser work when login, CAPTCHA/2FA, visible review,
   or extension state matters.
7. If the site remains blocked after the relevant Browserless path has actually
   run, say so plainly and name what was tried.

### Current Tab Or Logged-In Browser

1. Confirm that the task needs the user's live browser/session.
2. Use the available browser profile/node path for the target device.
3. If the requested mode is unavailable, say which capability is missing and
   choose the closest acceptable fallback.

## Bundled Helper Scripts

Use these from this skill directory when repeatable execution helps:

- `scripts/browserless_extract.py` - Browserless `content`, `unblock`, or `stealth-bql` using stdlib HTTP; reads `BROWSERLESS_TOKEN` or legacy `BROWSERLESS_API_KEY`; redacts tokens, retries transient failures, returns bounded excerpts, metadata, and generic media candidates. For Cloudflare/anti-bot pages, pass `--mode unblock` first. Note: OG/Twitter `meta` and `media_candidates` only populate in `content`/`unblock` modes — the default `stealth-bql` returns title/body text only, so pass `--mode content` or `--mode unblock` when you need metadata or media URLs.
- `scripts/browserless_media_requests.py` - Browserless `/function` network media discovery for rendered pages where media URLs appear only after playback/rendering
- `scripts/browserless_session.py` - opt-in persistent Browserless session helper with redacted output and 0600 session files
- `scripts/tinyfish_browser_extract.py` - optional TinyFish Browser API / CDP extraction helper

See `references/backends.md.example` for credential and command templates.

## Reference Files

- `references/context-device.md` - browser context/device/session matrix
- `references/extraction-backends.md` - backend ladder and safety notes
- `references/backends.md.example` - public-safe credential and command template

## Baseline Checks

Run `bash scripts/test.sh` after editing this skill.
