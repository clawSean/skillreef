# Browser Context Modes

Availability must be proved live. These modes describe intent, not guaranteed
runtime support.

## Current ClawPop matrix

| Context | Meaning | Current status |
|---|---|---|
| Fresh managed browser | isolated agent-controlled profile | proven; default unattended lane |
| Existing signed-in browser | attach to a real current session | built-in `user` route targets Chrome; custom supported Chromium-based profiles require setup, consent, and live proof |
| Shared current tab | user explicitly shares a tab to OpenClaw | Arc/Dia manual-WSS flow proved with the supported extension build; attachment remains live-state dependent |
| Arc or Dia fallback experiment | try a visible installed browser after a managed-browser block or capability gap | authorized; shared-tab builds have passed E2E, but the exact attachment must still be verified live |
| Visible manual handoff | user reviews, solves, approves, or takes over | available when direct control is unproved or the step must remain human-controlled |

## Preferred user-facing labels

- Fresh managed browser
- Your current browser
- Visible handoff

Do not expose internal transport names unless implementation details are
explicitly relevant.

## Consent boundaries

- Managed browser: agent-controlled isolated profile; verify account identity
  before authenticated work.
- Arc/Dia fallback canary: no-config testing through currently available app or
  UI controls is authorized after a managed-browser block or capability gap.
- Existing-session attachment: configuring or attaching a real browser profile
  requires a supported running browser, explicit setup, and local user approval.
- Shared-tab attachment: controls only tabs explicitly placed in the OpenClaw
  tab group; sharing the tab is a separate consent action.
- A direct request to use the shared/current tab pins that context. Do not switch
  to a managed profile or unrelated web route unless attachment is unavailable.
- Manual handoff: stop before the user-only step and state exactly what they
  need to review or complete.

## App truth rules

- Arc and Dia may be tried when the managed browser is blocked or lacks a needed
  capability.
- Arc running does not mean its page is attached, capturable, or controllable.
- Dia running does not mean its page can be captured or automated.
- Chromium ancestry or extension compatibility does not prove OpenClaw support.
- Brave is not installed on ClawPop.
- Never infer current login or attachment from historical VPS or node proof.

## Selection questions

1. Does the task need rendering, cookies, interaction, or a specific login?
2. Can search, fetch, or an API finish it more simply?
3. Is an isolated managed profile acceptable?
4. Did the managed browser fail in a way Arc or Dia might address?
5. Does the user need to see or take over the page?
6. Is the chosen capture or attachment path live and page-ready?
7. Is the next action external, irreversible, or approval-gated?

If the requested context is unavailable, say which capability is missing and
use the closest safe fallback.
