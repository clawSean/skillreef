# EdgeApp Cross-Repository Contract Playbook

Use when a change crosses repositories or changes a public API, cleaner,
persistence format, provider contract, native bridge, server policy, or release
sequence.

## Find the owning layer

Put the rule where its authoritative data lives:

- GUI and login UI own presentation, interaction, navigation, localization, and
  app-level orchestration.
- Core owns account/login/wallet contracts, plugin hosting, shared persistence,
  and public wallet APIs.
- Currency plugins own chain rules, address formats, transaction semantics,
  signing formats, and provider/node behavior for their chains.
- Exchange plugins own partner adaptation, amount/error mapping, and the spend
  information handed to wallets.
- Native repositories own platform SDK behavior, native paths, locks, binary
  formats, and bridge implementation.
- Servers own server-side policy, remote configuration, signing, and rate-limit
  enforcement.

Do not rederive owner data in the GUI with string parsing or parallel hardcoded
maps. Expose a typed owner-layer field or named error and keep the consumer
thin.

## Run the four-way compatibility matrix

For dependency version N and proposed N+1, reason about and test:

1. old dependency with old consumer;
2. old dependency with new consumer;
3. new dependency with old consumer;
4. new dependency with new consumer.

Unknown fields often cross cleaners. An old cleaner may silently delete a new
option, causing fallback behavior rather than a loud failure. Test that case
explicitly. Preserve the old default for existing callers and make the new path
opt-in unless the contract owner deliberately selects a breaking change.

If any mixed pair is unsafe, state the coupling, hold the consumer draft, and
ship both sides together. A successful N+1/N+1 test does not prove merge-order
safety.

## Sequence stacked work

- Open or prepare the owner/dependency change first.
- Keep the consumer integration draft or local until a consumable dependency
  exists.
- Cross-link both sides and name the exact version, tarball, commit, or future
  branch used for proof.
- Put the dependency pin and lockfile before consuming code in commit history.
- Rebase the consumer onto the released/merged dependency and repeat proof.
- For native work, verify both iOS and Android consumers unless the platform
  matrix is explicitly incomplete.
- Preserve authorship when incorporating a partner or another maintainer's
  commit; do not silently copy it into a new history.

## Contract and product gate

Explore contract options freely and prototype them locally when that will
clarify feasibility or tradeoffs. Label each shape as a candidate and preserve
the meaningful alternatives.

Before a public non-draft PR presents one as selected, get owner confirmation
for:

- new public fields or CLI/API names;
- persisted or synced shapes;
- broad UX ordering or monetization behavior;
- login, recovery, privacy, or security posture;
- provider behavior that fails a documented API requirement;
- intentionally coupled or staged releases.

A user-authorized public draft may be used deliberately to request that
decision; it is not evidence of approval. Keep a scenario-based decision log
for counterintuitive behavior. Tests should lock the chosen contract, not the
reviewer's initial preference. When the final decision changes, update earlier
replies and docs.

## Persistence, login, and multi-device behavior

Classify each state value by owner and lifetime:

- in-memory session;
- device-local encrypted state;
- account-synced state;
- server-only state;
- provider or chain state.

Test restart, logout/login, second device, stale local state, and network
unavailability where relevant. Do not call a device-local patch a multi-device
fix. Do not introduce optimistic healing when successful local login or later
sync already owns the recovery path.

Edge's local-first wallet access is an architectural invariant: a known device
should unlock available local account content without making Edge servers the
fund-access gate. Server contact can synchronize or provide fallback, but the
PR must say which path it proves.

When reviewers are not confident in auth or wallet-state behavior, stop and
trace actual reads, writes, clearing, and overwrite order before adding another
repair layer.

## Shared policies, fake worlds, and rollouts

A shared helper can serve production and fake/test routing. Before changing a
policy predicate:

- enumerate all callers;
- separate production security policy from explicit fake/test allowlists;
- list intentional adjacent behavior changes;
- test both accepted and rejected paths.

Distinguish a PR-introduced bug, a pre-existing bug, and a latent issue made
reachable by rollout. A latent issue can remain outside scope only with an
explicit pre-rollout gate, owner, and follow-up. Server-side enablement,
attestation enforcement, and rate-limit changes need their own rollout proof;
client green does not authorize activation.

## Provider and partner contract gaps

For provider integrations:

- verify chain identity, units, limits, address requirements, and asset support
  against current live authorized metadata and response shapes;
- distinguish client-fixable defects from adapter/API limitations;
- never synthesize guarantees or structured errors the provider did not supply;
- document unsupported reverse quotes, missing token identity, account
  activation uncertainty, or other contract gaps;
- obtain product sign-off when a mandatory provider requirement is not met;
- keep unsupported mappings explicit and prevent an outage from masquerading as
  an unsupported pair.

Fix what the client controls. Carry provider-side requirements as explicit
limitations or follow-ups rather than hidden heuristics.

## Completion gate

The cross-repo change is ready only when ownership is correct, all four version
combinations are safe or explicitly coupled, state lifetime is named, provider
or product gaps have owner decisions, dependency order is reproducible, and
proof covers the final released combination.
