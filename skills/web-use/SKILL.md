---
name: "web-use"
description: "Route web work by task category across local knowledge, domain tools, retrieval, cited research, managed browsing, public extraction, local apps, shared tabs, and GUI fallback."
---

# Web Use

Use this as the single front door for web work. First choose the **tool
category**, then load only that category's provider guidance. A provider failure
is never an overall web-capability verdict.

## Ownership contract

- `web-use` owns transport category, browser context, provider fallback,
  attachment proof, and lane-failure escalation.
- Domain skills own business intent, data semantics, account scope,
  credentials, preferences, and approval/action policy.
- `browser-automation` owns page-control mechanics only after this skill chooses
  a browser lane.
- `perplexity-search` owns Perplexity API, key, and preset mechanics after this
  skill chooses cited research.

When a domain skill applies, load it for domain rules and this skill for generic
web routing. Neither overrides the other's ownership. See
`references/domain-ownership.md`.

## Category waterfall

Start at the first row that fits the task. Leap directly to a specialist when
the task shape already proves it is better; do not make weaker lanes fail first.

| Task category | Default tool type | Load next |
|---|---|---|
| Prior local answer/proof | local knowledge or memory | `knowledge-search` + narrow source |
| Authoritative structured domain data | domain API/MCP/skill | active domain skill |
| Public discovery/current facts | native search | `references/research-routing.md` |
| Known public URL | native fetch | `references/research-routing.md` |
| Cited synthesis, comparison, difficult or broad research | specialist cited research | `perplexity-search` + `references/research-routing.md` |
| JavaScript, rendering, interaction, or local persistent login | managed browser | `references/context-device.md`, then `browser-automation` |
| Protected public page, crawl, or bulk structured extraction | hosted/public extraction | `references/extraction-backends.md` |
| Full local browser/app context genuinely required | local visible browser/app | `references/provider-matrix.md` + local registry |
| User explicitly requests their tab, must watch/participate, or requires exceptional sensitivity | shared-tab context | `references/shared-tab-extension.md` |
| Browser/DOM tools cannot reach a required native or OS surface | whole-desktop GUI | `references/context-device.md` + Peekaboo guidance |
| 2FA, passkey, CAPTCHA, payment, irreversible review, or missing authority | human gate | domain policy + visible handoff |

Expanded decision logic and next-hop states:
`references/decision-matrix.md`.

## Selective exposure

Load provider-specific files only after the category is selected:

- Research/retrieval → `references/research-routing.md`
- Managed/local/shared/GUI context → `references/context-device.md`
- Provider order and portable capabilities → `references/provider-matrix.md`
- Current machine/account/provider state → optional
  `references/provider-registry.local.md`, seeded from
  `references/provider-registry.local.example.md`
- Protected/bulk extraction → `references/extraction-backends.md`
- Shared-tab setup/diagnosis/release proof → `references/shared-tab-extension.md`
- Domain workflow → only the reference named by the active domain skill

The local registry is runtime state, not portable policy. If it is absent,
create it from the public example and prove entries locally. Verify it live
before authenticated or sensitive work. Never publish it or assume another
agent/machine inherits it.

## Core rules

1. Use the lightest dependable route that fits the task.
2. Optimize for accurate first-pass completion, not merely the cheapest call.
3. Prefer primary sources; inspect them before consequential claims or actions.
4. Treat paid/credit-consuming providers deliberately, using active free
   allowances first only when task fit and reliability are equivalent.
5. Keep authenticated state local by default. Do not export cookies, storage,
   or login sessions to hosted extraction providers without explicit approval
   and a domain policy permitting it.
6. Keep public extraction separate from interactive human-visible browsing.
7. Verify exact profile, account, visibility boundary, tab attachment, and final
   state. A click or command success is not proof the intended result occurred.
8. Never bypass CAPTCHA, 2FA, passkeys, payment approval, confirmation gates, or
   irreversible-action review.
9. Treat uninstalled, disabled, or unproved providers as candidates—not live
   fallbacks.

## Lane-failure escalation

Before saying a web task is blocked, classify the failure:

| Failure class | Next category |
|---|---|
| Missing source/data | domain tool → search/fetch → cited research |
| JavaScript/rendering | managed browser |
| Login/profile context | managed local profile → domain-approved visible context |
| Public anti-bot/protected extraction | hosted public extraction |
| Browser attachment/control | another live-proven provider in the same context category |
| Native app/OS surface | GUI/computer use after display/permission preflight |
| Human-only/security gate | visible handoff; state the exact user action |
| Provider outage/rate limit | next proven provider for the same category |

Check the active/deferred tool catalog, domain skill, provider registry, and
relevant fallback category. Do not repeat identical cheap retries. Stop only for
a genuine human gate, missing authority/credential, unacceptable risk, or
exhaustion of relevant proven lanes; name the remaining gate precisely.

## Context contracts

### Managed browser

Default for rendered, interactive, and authenticated unattended work. Persistent
profile state may exist, but verify live login/account state. Stop before any
approval-gated external action.

### Hosted extraction

Public data only by default. Choose provider/mode based on the actual blocker,
not provider novelty. A session primitive does not make hosted login persistence
desirable.

### Local visible browser/app

Use only when a full local profile, extension, browser-specific behavior, or
human-visible app context materially matters. Select from the local registry and
prove capture/control before relying on it.

### User's shared tab

Consent-bound and rare. When explicitly selected, pin that context and operate
only the shared tab. Do not detour into another browser, generic research, or
extension maintenance unless the shared context is unavailable or broken.

### Peekaboo / computer use

Last browser/GUI category, not last overall capability. It is slower and
token-expensive and requires an active unlocked graphical session plus required
permissions. A locked/no-display result is a GUI-lane gate, not proof the web
task is impossible.

## Truth and naming

- **Managed browser** — isolated agent-controlled profile.
- **Your current browser** — existing session only after live attachment proof.
- **Visible handoff** — user must review, solve, approve, or take over.

Keep transport/driver names out of user instructions unless implementation
details matter. Read `references/proof-policy.md` before changing routing or
making a capability claim; record new durable proof in the private local ledger
and update the local registry at the moment reality changes.

## References

- `references/decision-matrix.md` — categorical waterfall and next-hop logic
- `references/research-routing.md` — native retrieval vs cited research
- `references/provider-matrix.md` — portable ordered providers by category
- `references/provider-registry.local.example.md` — portable registry template
- `references/provider-registry.local.md` — optional private host/account state
- `references/domain-ownership.md` — domain/web boundary and backlink contract
- `references/context-device.md` — browser/device consent and selection
- `references/extraction-backends.md` — public extraction modes and economics
- `references/shared-tab-extension.md` — rare extension operations branch
- `references/proof-policy.md` — portable admission and regression rules
- `references/proof-ledger.local.example.md` — portable proof-ledger template
- `references/proof-ledger.local.md` — optional private dated proof and gaps
