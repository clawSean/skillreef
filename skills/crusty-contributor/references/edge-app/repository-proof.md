# EdgeApp Repository Proof Playbook

Use the matching section after the general Edge preflight. Current target-repo
AGENTS.md, review rules, package scripts, and architecture docs remain the
source of truth.

## GUI and login UI

Before editing:

- inspect every consumer of a shared component, hook, locale key, selector, or
  navigation route;
- scope behavior with an explicit prop or route when account creation, upgrade,
  and existing-account flows reuse the same component;
- search existing localization keys and run the repository localization
  workflow;
- use current shared themed primitives, spacing rules, accessibility patterns,
  and useHandler conventions.

For stateful UI, cover the lifecycle that can reach it:

- cold launch and warm/deep-link delivery;
- back navigation and repeated entry;
- leaving the tab or screen;
- configuration refresh;
- loading, failure, empty, disabled, cancellation, and rapid repeat;
- small and large screens, localization expansion, keyboard, safe areas, iOS,
  and Android.

Audit Maestro or test-only branches. If production behavior differs under an
isMaestro check, actual Maestro execution is not enough; run a non-Maestro
device path too. Label any forced state or local configuration and state that a
screenshot proves pixels, not reachability.

For ordering, badges, rate claims, promotion, or monetization, verify that every
display claim stays true after sorting. Turn disagreements into product
decisions with worked scenarios.

## Core, account, login, and storage

For public APIs, preserve existing behavior through a wrapper or opt-in field
when possible. Test fake plugins and multiple plugin/wallet instances, not only
the happy concrete implementation.

For storage changes:

- use the repository's current data-store API;
- make new persisted fields optional or provide a migration;
- preserve sibling keys during nested updates;
- reset module caches across logout/login;
- test old data, missing data, malformed data, restart, and second-device
  behavior.

For async services and engines, test stale attempts, generation guards,
cancellation after every await, expiry/backoff, partial start, shutdown,
resource cleanup, and repeated start. If start opens a handle and later throws,
close the handle before surfacing the failure.

Do not force a generic periodic-task abstraction when settle timing, variable
delay, or cancellation semantics differ. Explain the mismatch and test the race
the local implementation prevents.

Audit shared policy helpers against fake/test infrastructure. Export
platform-owned paths or constants across the native bridge instead of
hardcoding platform paths in JavaScript.

Login and recovery changes require architectural confidence. Trace which layer
owns local unlock, server fallback, sync, and state clearing. If a test passes
for an accidental setup line or the team is unsure which overwrite wins, stop
and re-derive the state machine.

## Currency and native plugins

Read the current chain implementation, shared engine conventions, native
adapter, and authoritative upstream protocol source before changing funds or
identity behavior.

Required proof scales with risk:

- amount and fee math: native/token cases, minimum/maximum, rounding, success,
  failure, and zero;
- history: signer, recipient, unrelated address, failed transaction, fee-only
  outcome, pagination, checkpoint, resync, and partial-page failure;
- seed/address/signature: deterministic vectors, normalization, checksum,
  protected/unprotected cases, independent round-trip verification, preserved
  defaults, and a loud owner/native mismatch guard;
- nodes: live authorized responses, archival versus pruned behavior, timeout,
  all-dead pool, stale node, rate limits, cursor commits, and retry;
- native lifecycle: both platforms, lock/queue behavior, already-open recovery,
  start failure cleanup, platform-native formatting, and actual app integration.

Use vendored provider/chain snapshots for regressions, but also test the small
mapping helper in isolation. Never accept a live fixture blindly: clean it and
document provenance without embedding secrets or private user data.

Put chain-specific prefixes, address types, derivation formats, and transaction
classification in the plugin or native owner. Do not duplicate them in GUI
maps. If a JS and native derivation disagree, fail before sync rather than
opening a wallet whose displayed identity is wrong.

## Exchange and provider plugins

Before implementation or review, read the current exchange repository:

- AGENTS.md;
- .cursor/BUGBOT.md;
- docs/CREATING_AN_EXCHANGE_PLUGIN.md;
- docs/API_REQUIREMENTS.md;
- docs/CHAIN_MAPPING_SYNCHRONIZERS.md when mappings change;
- the current central template and nearest reviewed provider.

Treat the template as executable guidance. Copy its tests and comments for the
constructs retained. When a review finding recurs across providers, improve the
template, helper, tests, or repo rules rather than fixing the next plugin alone.

At minimum prove:

- integer atomic units, directional rounding, and biggystring comparisons;
- requested-amount bounds on every provider field that reaches a signed spend;
- quote-only max probes, skipChecks, and no abandoned order when the API allows;
- numeric/string/blank memo and error-code shapes;
- correct fixed-versus-estimate reporting and expiry/backoff behavior;
- provider outage versus unsupported-pair classification;
- live chain identity, token contracts, native assets, address types, and
  account-activation requirements;
- one real quote path and authorized negative responses against the current API;
- built bundle plus GUI updot/debug-bundle integration.

Plugins execute inside core's plugin WebView, not the React Native debugger.
Plan for bundle rebuilds and plugin logs. If a template/docs-only change leaves
the production bundle byte-identical, prove that exact fact; app testing would
not exercise it.

Do not use real funds, production keys, or unsupported accounts solely for
proof. If an end-to-end swap is authorized, record pair, direction, quote type,
and outcome without publishing credentials or sensitive addresses.

## Proof escalation

Use the lowest layer that proves the claim, then escalate for remaining risk:

1. static checks and focused unit/property tests;
2. full repository verification and built artifact;
3. owner/consumer integration with the exact dependency version;
4. simulator or device lifecycle proof;
5. authorized live provider or chain proof;
6. release/production proof only with explicit release authority.

Report every skipped layer as unproven. A stronger-looking layer does not
replace a precise lower-layer invariant test.
