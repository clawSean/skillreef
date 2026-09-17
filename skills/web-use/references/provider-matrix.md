# Portable Provider Matrix

This file defines preferred provider order within each category. Current host,
account, login, install, balance, and proof state live only in
`provider-registry.local.md`.

| Category | Preferred provider order | Selection rule |
|---|---|---|
| Native discovery | configured OpenClaw search → another enabled native search provider | use current configured provider; do not mutate config merely to route one query |
| Known public URL | OpenClaw fetch/readability → managed browser | escalate only for JS/rendering/interaction |
| Cited research | installed specialist cited-research skill → native search plus primary-source synthesis | use specialist early when breadth/reasoning/completeness matters |
| Managed interaction/auth | OpenClaw managed profile → another live-proven managed profile | verify profile/account live |
| Protected public extraction | stateless anti-bot extractor → deeper hosted browser → installed crawl/actor provider | choose mode/provider by blocker, breadth, and cost |
| Existing browser session | lowest-priority-number context-fit `existing-session` profile with live attachment/control proof | use only when daily-profile context materially matters; an attach prompt is a human gate |
| Local visible browser/app | lowest-priority-number installed context-fit app with live capture/control proof | local registry owns exact order; skip any row that fails fit or proof |
| Native GUI/OS | installed computer-use provider with active display/permissions | preflight display, permission, and target capture |
| Extension-relay shared tab | the explicitly requested tab on a live-proven extension profile | verify `Selected tabs`/`All tabs`, inventory, and control; absent explicit selection, relevant self-sufficient GUI lanes come first |
| Domain structured data | owning domain API/MCP/skill | domain owner defines its provider order |

## Provider admission states

- `proven` — current runtime plus representative live task passed.
- `configured-unproven` — tool/credential/config exists but runtime/task proof is
  incomplete.
- `candidate` — potentially useful but uninstalled, disabled, or unevaluated.
- `unavailable` — current environment cannot use it.
- `retired` — intentionally removed; never silently revive.

Only `proven` providers may be automatic fallbacks. A
`configured-unproven` provider can be tested when the task justifies a bounded
canary. Installation, config mutation, and service restart remain separately
approval-gated.

## Local priority contract

Every provider-registry row has an explicit positive-integer `Priority`.
Lower numbers are preferred **within the same category**, after task fit,
privacy, authority, and proof gates pass. Use gaps such as `10, 20, 30` so a
new provider can be inserted without rewriting unrelated rows. Never compare
priority numbers across categories.

## Cost posture

Use active free allowances first when fit/reliability are equivalent. Paid use
is appropriate when it materially improves accuracy, coverage, or completion
time. Cost priority never overrides privacy boundaries or causes repeated
low-quality attempts.

## Existing-session limitations

Managed profiles are the full-featured default. In current OpenClaw, the
`existing-session` driver (including built-in `profile="user"`) uses refs and a
shared action budget; it does not support `networkidle`, batch actions,
response-body capture, download interception, or PDF export, and several acts
reject per-call timeout overrides. Page/ref screenshots work, but CSS-element
screenshots do not. Before selecting it, load current `browser-automation`
guidance because this list can change between releases.

The extension driver is a separate lane (built-in `profile="chrome"` in current
OpenClaw). Its authenticated relay, access mode, returned tab inventory, and
page control are separate proof states. Never infer a selected-tab boundary
from successful pairing alone.
