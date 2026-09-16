# Shared-Tab Extension Operations

Load this reference only for shared-tab setup, pairing, connection diagnosis,
credential rotation, branding, compatibility proof, or release work. Ordinary
page control uses `browser-automation` after `web-use` selects the shared-tab
lane.

## State model

Keep these facts separate:

1. **Configured** — pairing data is stored.
2. **Relay connected** — the extension has an authenticated Gateway socket.
3. **Tab selected** — the browser granted debugger access to a local tab.
4. **Tab published** — Gateway inventory exposes the intended tab.
5. **Page controllable** — a fresh snapshot or action succeeds.

Never infer a later state from an earlier one. A selected tab is not proof of a
connected relay, and a listed tab is not proof of page control.

## Normal shared-tab use

1. List current shared tabs and identify the intended tab without opening or
   researching elsewhere. Continue only when its identity is unambiguous.
2. Take a fresh snapshot. Report attachment failure plainly if it cannot read
   the page.
3. Load `browser-automation` for multi-step control, stale-ref recovery, tab
   hygiene, and action verification.
4. Preserve the user's chosen browser context. Ask before navigating away when
   that would disrupt their visible work, and restore temporary navigation.
5. Verify the final page/tab state before claiming completion.

## Setup and pairing

1. Use a permanent unpacked extension directory with one identity per agent.
   Separate branded agents must not share storage keys, tab-group labels,
   pairing state, or Gateway credentials.
2. For manual remote WSS pairing, disable automatic local setup so two
   connection authorities do not compete.
3. Deliver pairing credentials only through a trusted private channel. Never
   echo them into a group, screenshot, log, normal temp file, or tool result.
4. Treat any visibly exposed pairing credential as compromised. Follow current
   OpenClaw docs and the operator's restart/config approval policy before
   rotating or revoking it.
5. Call setup complete only after the E2E gate below passes on the target
   machine.

## Diagnosis order

1. Read Settings and popup state as separate observations; neither alone proves
   control.
2. Check authenticated relay state and Gateway tab inventory.
3. Confirm exactly the intended tab is selected and published.
4. Attempt a fresh snapshot, then one harmless reversible action.
5. Diagnose pairing, relay, tab publication, and page-control failures at their
   owning layer. Do not repair OpenClaw, change live config, or restart the
   Gateway without the required approval.

## E2E and release gate

Prove the exact packaged artifact, not only its source tree:

1. pair through the real Settings manual-WSS path;
2. observe Settings move to authenticated relay state without reopening;
3. publish exactly one HTTPS tab;
4. list and snapshot that tab;
5. perform one harmless reversible page action;
6. disconnect and verify Gateway inventory returns to zero;
7. reconnect without a new code and repeat the snapshot;
8. clean disposable profiles and verify no credential entered logs or artifacts.

Keep versioned build, branding, test, checksum, and release instructions in the
canonical extension project. Sean's public repository is a **reference
implementation**, not an install artifact for another agent:
<https://github.com/clawSean/openclaw-arc-dia-browser-extension>. A non-Sean
agent must use its separately branded build/handoff with isolated storage and
pairing state.

Use the installed OpenClaw documentation as runtime authority for Gateway and
extension commands; the project proves the custom distribution, not future
OpenClaw compatibility.
