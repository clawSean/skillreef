# Browser and Device Contexts

Choose context independently from information provider. Availability must be
proved live; these modes express intent, not guaranteed runtime support.

| Context | Use when | Required proof |
|---|---|---|
| Managed browser | ordinary rendered, interactive, or authenticated unattended work | process/profile page-ready; intended account/login verified |
| Existing-session driver | a daily Chromium profile's cookies or browser-specific context matters | exact `existing-session` profile; any attach prompt resolved; page capture/control live |
| Local visible browser/app | a specific local app/profile is required but no browser driver can supply the context | selected provider installed; unlocked display; app/page capture and control live |
| Whole-desktop GUI | browser/DOM tools cannot reach browser chrome, native app, or OS dialog | active unlocked display, permissions, target capture |
| Extension-relay shared tab | user explicitly requests it, must watch/participate, exceptional sensitivity requires their context, or relevant self-sufficient lanes failed and the user agrees to share | authenticated relay, access mode, exact published tab, snapshot/control |
| Visible handoff | user-only security/approval/review step remains | exact requested human action and safe resume point |

## Selection questions

1. Does the task need rendering, cookies, interaction, or a specific login?
2. Can local knowledge, a domain tool, search/fetch, or cited research finish it
   without a browser?
3. Is the managed isolated profile acceptable and live for the intended account?
4. Does an existing-session driver supply a required daily-browser context
   without exporting it or asking the user to share a separate tab?
5. Does a full local visible browser/app context materially solve a remaining
   capability or profile gap?
6. Is the remaining surface browser chrome/native GUI rather than webpage DOM,
   and can computer use reach it without user initiation?
7. Did the user explicitly select their current/shared tab, must they actively
   watch/participate, or have relevant self-sufficient lanes proved unfit?
8. Is the next step human-only, external, irreversible, or approval-gated?

## Consent and privacy boundaries

- Managed browser: agent-controlled local isolated profile; verify account
  identity before authenticated work.
- Existing-session driver: use only the selected provider/profile after live
  proof; installed/running is not attached/controllable. Current OpenClaw's
  built-in `user` profile uses Chrome MCP and is distinct from the extension
  relay.
- Extension relay: verify `Selected tabs` versus `All tabs` and the returned
  inventory. Official fresh automatic pairings may default to `All tabs`; do
  not claim a one-tab privacy boundary merely because the user named one tab.
- Shared tab: pins the user's requested tab operationally even if the relay's
  technical access is broader. Touch no other published tab.
- Hosted extraction: public data only by default; do not export local session
  state into it.
- GUI control: requires unlocked graphical session and target-specific capture.
- Shared-tab initiation is a human action. Unless the user explicitly requests
  that context, attempt relevant self-sufficient GUI control before asking them
  to share a personal tab.
- Handoff: stop before the user-only step and state exactly what to complete.

## Shared-context pinning

When the user requests their current/shared tab, do not silently substitute a
managed profile, another local browser, hosted extractor, or unrelated research
lane. If the attachment is unavailable, report that specific gap and offer safe
alternatives; do not re-pair/repair unless the user asks or the requested lane
cannot operate.

## Live provider selection

Use `provider-matrix.md` for portable order and
`provider-registry.local.md` for this installation's exact provider rank,
status, login/context notes, and proof requirements. Never infer current state
from historical node, VPS, browser, or extension evidence.
