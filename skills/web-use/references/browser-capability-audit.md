# ClawPop Browser Capability Audit

Verified 2026-09-15. Treat runtime status as volatile and recheck before a
sensitive or authenticated task.

## Verdict

Use the managed browser for maximum proven unattended control. Use the
shared-tab extension when the user requests their current browser, existing
login, or a specifically shared tab.

The supported Arc/Dia extension build passed manual-WSS pairing, one-tab
publication, semantic snapshot, page action, disconnect-to-zero, and reconnect
proof against OpenClaw 2026.9.4. This proves the architecture, not the current
attachment; recheck live state for each task.

Among Arc, Dia, and Brave, Brave is the strongest future dedicated visible-agent
candidate. It is not installed and remains approval-gated.

## Live capability matrix

| Lane | Proven now | Persistence | Gaps |
|---|---|---|---|
| Managed browser | launch, navigation, ARIA snapshot, labeled screenshot, typing, clicking, evaluation, guarded upload, download | dedicated profile state survived stop/start | headless; live site login must be checked; alert detection worked but alert acceptance hung in the canary |
| Existing-session lane | built-in `user` route targets Chrome; custom supported Chromium-based profiles are documented | would reuse a real browser profile | each setup still requires consent and live proof |
| Shared-tab extension lane | manual-WSS pairing, one-tab publication, snapshot, action, disconnect, and reconnect passed | reuses the shared tab's signed-in state | current relay and tab attachment must be checked live |
| Arc | supported shared-tab build passed E2E | Arc retains its own local profile | running is not attachment; user must explicitly share a tab |
| Dia | supported shared-tab build passed E2E | Dia supports its own profiles | running is not attachment; user must explicitly share a tab |
| Brave | not installed | not applicable | installation, isolated profile, and live OpenClaw smoke test require explicit approval |

## Managed-browser proof

The 2026-08-30 canary:

- opened a public page and produced an ARIA snapshot and labeled screenshot;
- typed into an injected benign form and clicked its button;
- preserved local profile storage across stop/start;
- uploaded an inbound-media file through a file input;
- downloaded a generated text file and verified its content;
- detected a JavaScript alert, but the accept operation hung;
- cleaned the canary page state and moved scratch artifacts to Trash; browser
  lifecycle state was not reliably restored or verified, so recheck live status
  instead of inferring it from this audit.

Do not describe alert handling as reliable until the accept path passes a fresh
canary.

## Installed runtime facts

- OpenClaw 2026.7.1
- `playwright-core` 1.61.1
- managed profile: Mac-local, headless, `noSandbox:false`
- detected internal executable: Google Chrome 151
- dedicated stable managed-profile data directory
- current browser work is Gateway-local on ClawPop
- no usable browser node was connected during the sweep
- node browser routing was observed as `manual` in live config readback

Internal executable names are not user-facing browser instructions.

## Attachment and consent

The built-in `user` existing-session lane targets Google Chrome. Custom
existing-session profiles can target supported Chromium-based browser profiles
through a configured user-data directory; each target still requires explicit
setup, local consent, and live smoke proof. The reduced existing-session
capability surface excludes PDF, downloads, and response body retrieval.

The shared-tab extension lane is Chrome-specific in current documentation.
It controls only tabs in the OpenClaw tab group. Sharing a tab into that group is
the consent boundary.

Do not describe Arc, Dia, Brave, or a generic Chromium app as compatible merely
because it can run extensions or is Chromium-based.

## Arc, Dia, and Brave evaluation

### Arc

- Installed and the reviewer's normal visible browser.
- Local profiles retain logins and cookies.
- Core product development is in maintenance mode.
- No vendor-supported external automation contract or live OpenClaw attachment
  was proved.

Use for ordinary human browsing and as an authorized fallback when the managed
browser is blocked. Begin each automated attempt with a live page capture and
control canary; use manual handoff if that proof fails.

### Dia

- Installed and actively developed.
- Supports profiles and extensions.
- Native agent safeguards require review for writes and restrict sensitive or
  irreversible controls.
- Chromium ancestry does not prove external attachment.

Keep as a human-facing AI browser and authorized fallback experiment. Begin
each automated attempt with a live page-level or macOS visual-control smoke
test; use manual handoff if that proof fails.

### Brave

- Not installed.
- Publishes command-line remote-debugging support.
- Supports Chromium extensions and encrypted sync.
- Has the strongest mature automation substrate of these three.

If the reviewer approves a future visible-agent lane, use a dedicated headed profile,
bind debugging to loopback, keep it separate from the personal profile, and
smoke-test OpenClaw attachment before trusting it. The current OpenClaw
shared-tab extension documentation still favors Chrome, so Brave extension
relay compatibility is unproved.

## Honest limits

No browser provides literally uninhibited access. CAPTCHA, 2FA, passkeys,
anti-bot systems, provider policies, approval gates, and site-specific changes
remain real boundaries.

## Primary sources

- OpenClaw browser docs: https://docs.openclaw.ai/tools/browser
- OpenClaw extension docs: https://docs.openclaw.ai/tools/chrome-extension
- Brave command-line flags:
  https://support.brave.com/hc/en-us/articles/360044860011-How-Do-I-Use-Command-Line-Flags-in-Brave
- Brave extensions:
  https://support.brave.com/hc/en-us/articles/360017909112-How-can-I-add-extensions-to-Brave
- Dia security: https://www.diabrowser.com/security
- Dia privacy: https://www.diabrowser.com/privacy
- Arc profiles:
  https://resources.arc.net/hc/en-us/articles/19227964556183-Profiles-Separate-Work-Personal-Browsing
- Arc maintenance strategy:
  https://browsercompany.substack.com/p/letter-to-arc-members-2025
