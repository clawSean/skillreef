---
name: "web-use"
description: "Route web work across local knowledge, search/fetch, cited research, managed browsing, public extraction, browser apps, shared tabs, and GUI fallback."
---

# Web Use

Use this as the single front door for web work. Choose these independently:

1. **Information path:** local knowledge, search/fetch, cited research, extraction,
   or a domain API.
2. **Interaction context:** managed profile, local browser app, explicitly shared
   tab, or whole-desktop GUI.

Do not choose a browser just because one is installed or running. Do not treat a
failure in one lane as an overall web capability failure.

## Default priority

| Need | Start with |
|---|---|
| Existing local knowledge or prior proof | `knowledge-search` / memory |
| Discover sources or current facts | native `web_search` |
| Read a known public URL | native `web_fetch` |
| Cited synthesis, multi-source comparison, or difficult research | `perplexity-search` |
| JavaScript, rendering, interaction, or persistent login | OpenClaw managed browser |
| Public anti-bot page or bulk structured extraction | `references/extraction-backends.md` |
| Full local browser/app context is genuinely required | local browser automation |
| The user explicitly requests their shared tab, must watch, or must keep an exceptionally sensitive workflow off the agent-managed profile | shared-tab extension |
| Browser tools cannot reach the needed GUI/OS surface | Peekaboo / computer use |
| Authoritative structured data or site policy exists | relevant domain skill/API |

This is a priority order, not a ritual. Leap directly to a specialist when the
task shape already proves it is the right lane. Do not waste time making a
simpler route fail first.

## Tool-guidance loading

Load only the guidance for the chosen lane:

| Chosen lane | Load next |
|---|---|
| Local recall | `knowledge-search` and the narrow memory/knowledge source |
| Search or fetch | matching native tool; no browser skill |
| Cited research | `perplexity-search`; the primary agent still verifies consequential claims |
| Managed browser or page-level local/shared control | `browser-automation` for mechanics |
| Protected/bulk public extraction | `references/extraction-backends.md` |
| Login/profile/device selection | `references/context-device.md` |
| Shared-tab setup, pairing, diagnosis, or release proof | `references/shared-tab-extension.md` |
| GUI/desktop fallback | Peekaboo/computer-use guidance plus `references/context-device.md` |
| Site-specific workflow | relevant domain skill |

`browser-automation` owns page-control mechanics only after this skill chooses a
browser lane. It must not silently replace search, fetch, cited research, an API,
or the browser context requested by the user.

## Research and retrieval

### Native search and fetch

- Use `web_search` for discovery, current facts, links, and source finding.
- Use `web_fetch` for known public pages that do not need JavaScript or login.
- Prefer primary sources and fetch them before relying on snippets for
  consequential claims.
- A domain tool may leapfrog generic search when it is clearly more
  authoritative or structured.

### Perplexity cited research

Use the standalone `perplexity-search` skill early—not merely after failure—when
the task benefits from source-backed synthesis, broad discovery, comparison,
multi-hop reasoning, or exhaustive coverage. Use the narrowest sufficient
preset. Perplexity is a research analyst lane; the primary agent owns final interpretation
and checks material primary sources.

Routine URL retrieval remains native search/fetch. Do not spend a Perplexity
call duplicating a simple fact or known-page read.

### Scraping and extraction

Scrapers are for protected pages, repeated structured collection, or bulk
extraction—not routine exploration. Keep native search/fetch and Perplexity as
the primary discovery/research paths.

Prefer active free allowances before paid calls when reliability is equivalent,
but never burn time looping on a cheap route whose task fit is wrong. Treat
uninstalled providers as candidates, not capabilities.

## Browser and interaction lanes

### Managed browser

Use the managed browser for ordinary rendered pages, deterministic interaction,
screenshots, uploads/downloads, and both public and authenticated work. Its
isolated profile can persist state, but verify the live account and login before
acting.

Stop before purchase, send, publish, delete, credential change, or other
approval-gated action. Detection or a click is not proof of completion; verify
the resulting state.

### Hosted public extraction

Use Browserless first for stateless protected extraction; select `/unblock` or
`/stealth/bql` according to the blocker. Use TinyFish when deeper hosted
multi-step public-browser control is needed.

Do not export cookies or maintain authenticated logins in Browserless, TinyFish,
or another remote provider by default. Privacy, cost, and cross-session
reliability make the agent-managed profile the authenticated lane. Any exception
needs explicit user authorization and an owning domain policy.

### Local browser apps

Use a real local browser/app-control path only when the managed browser or data
lanes cannot supply browser-specific behavior, a full local profile, extension
state, or a human-visible local context. Prove page capture and control live.

### The user's shared tab

The shared-tab extension is consent-bound and intentionally rare. Use it when:

- the user explicitly asks to operate the shared/current tab;
- he must actively watch, review, or participate; or
- the workflow is exceptionally sensitive and should not run in the agent-managed
  profile.

When selected, pin that context and operate only the shared tab. Do not detour
into unrelated research, another browser, or extension maintenance unless the
shared context is unavailable or broken.

### Peekaboo / computer use

Use whole-desktop control when DOM/browser tools cannot reach browser chrome, a
native app, OS dialog, or other required GUI. It is slower and token-expensive.
It also requires an active unlocked graphical session; a locked Mac may expose
no display. Ask for unlock when needed, but continue evaluating other lanes
before declaring the task blocked.

## Anti-bot and human gates

1. For a public protected page, try the managed browser if normal rendering may
   work.
2. For extraction-only blocks, use Browserless stateless modes, then TinyFish
   for deeper hosted control.
3. Use a local visible browser only when local browser context materially helps.
4. Use the shared tab only under its explicit/sensitive/watch-required policy.
5. CAPTCHA, 2FA, passkeys, payment approval, and irreversible review remain
   human gates; never claim or attempt to bypass them.

## Never incorrectly declare “blocked”

Before saying a web task cannot be done, classify the failure:

- missing information/data path;
- rendering or JavaScript;
- authentication/profile context;
- anti-bot protection;
- browser attachment/control;
- GUI/display access;
- human approval or authority.

Then check the active and deferred tool catalog, the relevant domain skill,
native search/fetch, cited research, managed browser, protected extraction,
local app control, shared handoff, and GUI fallback as appropriate. A provider
timeout, stale accessibility reference, locked display, or detached tab is a
lane failure—not proof of inability.

Stop only for a genuine human gate, missing authority/credential, unacceptable
risk, or exhaustion of the relevant lanes. State exactly which gate remains.

## Browser truth and naming

- **Managed browser** — isolated agent-controlled profile.
- **Your current browser** — an existing signed-in tab/session only after live
  attachment proof.
- **Visible handoff** — the user must review, solve, approve, or take over.

Keep driver/transport names out of user instructions unless implementation
details matter. A running browser is not an attached page. Recheck live status
for every sensitive or authenticated task.

Read `references/browser-capability-audit.md` before changing browser routing,
configuring an attachment, or making a capability claim.

## Bundled helpers

- `scripts/browserless_extract.py` — Browserless content, unblock, or stealth BQL
- `scripts/browserless_session.py` — opt-in public persistence with redacted
  output and `0600` session files
- `scripts/tinyfish_browser_extract.py` — TinyFish browser-session extraction

## References

- `references/browser-capability-audit.md` — current proof and honest gaps
- `references/context-device.md` — context, consent, and attachment matrix
- `references/shared-tab-extension.md` — rare setup/diagnosis/proof branch
- `references/extraction-backends.md` — provider ladder, cost posture, and safety
- `references/backends.md` — machine-local backend notes (never publish)
- `references/backends.md.example` — public-safe setup template
