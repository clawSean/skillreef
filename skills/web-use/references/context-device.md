# Browser and Device Contexts

Choose context independently from information provider. Availability must be
proved live; these modes express intent, not guaranteed runtime support.

| Context | Use when | Required proof |
|---|---|---|
| Managed browser | ordinary rendered, interactive, or authenticated unattended work | process/profile page-ready; intended account/login verified |
| Existing local browser session | a particular local profile, extension, or browser-specific behavior matters | selected provider installed; page capture/control live |
| Whole-desktop GUI | browser/DOM tools cannot reach browser chrome, native app, or OS dialog | active unlocked display, permissions, target capture |
| Shared current tab | user explicitly requests it, must watch/participate, exceptional sensitivity requires their context, or relevant self-sufficient lanes failed and the user agrees to share | authenticated relay, exact shared tab, snapshot/control |
| Visible handoff | user-only security/approval/review step remains | exact requested human action and safe resume point |

## Selection questions

1. Does the task need rendering, cookies, interaction, or a specific login?
2. Can local knowledge, a domain tool, search/fetch, or cited research finish it
   without a browser?
3. Is the managed isolated profile acceptable and live for the intended account?
4. Does a full local visible browser/app context materially solve a remaining
   capability or profile gap?
5. Is the remaining surface browser chrome/native GUI rather than webpage DOM,
   and can computer use reach it without user initiation?
6. Did the user explicitly select their current/shared tab, must they actively
   watch/participate, or have relevant self-sufficient lanes proved unfit?
7. Is the next step human-only, external, irreversible, or approval-gated?

## Consent and privacy boundaries

- Managed browser: agent-controlled local isolated profile; verify account
  identity before authenticated work.
- Existing local session: use only the selected provider/profile after live
  proof; installed/running is not attached/controllable.
- Shared tab: controls only explicitly shared tabs. Sharing is a separate
  consent action and pins the requested context.
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
