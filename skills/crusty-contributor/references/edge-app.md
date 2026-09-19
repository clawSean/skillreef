# EdgeApp Contribution Overlay

Use for `EdgeApp/*` repositories and changes consumed by Edge Wallet across GUI,
core, currency, exchange, login, info-server, or native-binding repositories.
This file holds Edge-specific contribution rules; the skill body stays generic.

## Authority and freshness

Synthesized from the August 24, 2026 contributor guide compiled from current
public and authorized private repositories. Treat it as routing guidance, not
immutable organization policy.

When sources conflict:

1. Current target-repo `AGENTS.md`, `package.json`, lockfile, source, README,
   and PR template.
2. Authorized current `edge-dev-agents/.cursor/` implementation/review rules.
3. Current Git and React guidance in `edge-conventions`.
4. Shared templates and automation in `edge-workflows`.
5. Legacy Yarn, Flow, Airbitz, AppCenter, or inherited contribution docs only
   as historical context.

Re-check the actual default branch, dependency graph, and scripts every time.
Snapshot versions, issue numbers, and commands are not standing contracts.

## Deep guidance routes

After the Edge preflight, load the narrow playbooks that match the change:

- Every PR we author or materially update: read
  references/edge-app/proof-contract.md. This is our self-imposed contributor
  standard, not a claim about Edge organization policy.
- Any non-trivial implementation, review, or PR: read
  references/edge-app/review-proof.md.
- Any dependency/consumer pair, public API, cleaner-crossing field, persistence
  change, provider/partner contract, native bridge, or server policy: also read
  references/edge-app/cross-repo-contracts.md.
- For GUI/login, core/auth, currency/native, or exchange/provider work: read the
  matching section in references/edge-app/repository-proof.md.

These routes are mandatory when their trigger applies. Current target-repo
source and instructions still override the synthesized playbooks.

## Private-source boundary

The source packet mixes public and private repositories.

- Classify every source before quoting, linking, or publishing it.
- Keep private repo names, org inventory, plans, acceptance criteria, internal
  endpoints, and unpublished security findings local unless an Edge owner
  authorizes disclosure.
- Public artifacts must stand on public reproduction, code, and documentation.
  Never cite a private source as the public justification.
- Serious security findings stop public work and go privately to the current
  security owner or documented security channel.

## Edge preflight and contract gate

1. Identify the user job, owning repo, target branch, issue/PR, and whether the
   request is implementation, review, or product-contract work.
2. Run the generic redundancy check against current source, issues, open/closed
   PRs, changelog, and releases.
3. Read target `AGENTS.md`, package metadata, lockfile, PR template,
   `.cursor/BUGBOT.md` or rules, and touched architecture docs.
4. Confirm source visibility and sanitize private-only evidence before any
   public action.
5. Trace the behavior to the repository actually consumed by the GUI; an
   unarchived standalone currency repo may be superseded.
6. Suggest and compare new API/CLI fields, persistence formats, cross-repo
   protocols, broad UX directions, and security-posture options freely. Build
   local prototypes when they clarify feasibility or tradeoffs; label them
   candidate designs, not selected Edge contracts. Product-owner alignment is
   required before a public non-draft PR represents one as selected, and before
   breaking, persisted, security, or release decisions proceed. A public draft
   is optional as a deliberate discussion surface, never proof of approval.
7. On a maintainer-owned initiative branch, confirm both the base and whether
   contributions are wanted. An experimental branch is not an invitation to an
   unsolicited public PR.

## Repository ownership baseline

Always verify current GitHub metadata. The August 2026 baseline is:

- `edge-react-gui`: `develop`; presentation, navigation, localization, app
  configuration, GUI wiring, and app-level tests.
- `edge-core-js`: `master`; account, login, wallet, data-store, and plugin-host
  behavior.
- `edge-currency-accountbased`: `master`; account-based networks and native
  adapter entry points.
- `edge-currency-plugins`: `master`; Bitcoin-family and other UTXO plugins.
- `edge-exchange-plugins`: `master`; rates, swaps, and provider plugins.
- `edge-login-ui-rn`: `master`; reusable login/account UI.
- `edge-info-server`: `master`; remote config, signing, and attestation server
  behavior.
- Relevant `react-native-*` repo: native execution; defaults vary between
  `main` and `master`.

## Cross-repository changes

- Put the root change in the owning core, plugin, server, or native repo.
- Open that dependency PR first and the GUI integration/version PR second.
  Cross-link both and keep the GUI PR draft until the dependency is consumable.
- Honor synchronization notices shared with `edge-login-ui-rn`; patch and
  verify both repos when required.
- Prove plugin behavior in its repo, build its bundle, then verify through the
  GUI using the supported debug-bundle or `updot` path.
- Native dependency changes require current Android and iOS integration proof.

## Git and review workflow

- Branch from the current default unless resuming a PR or a maintainer selected
  an initiative branch.
- Commit subjects are imperative, capitalized, no period, and at most 50
  characters. Bodies explain what/why and wrap near 72 columns.
- Keep each commit buildable; separate renames from behavior and remove WIP
  history before review.
- For review changes, prefer one `fixup!` per target commit per review round,
  one push per round, then autosquash.
- Do not rewrite, resolve, or land another author's PR without authorization.
- Edge future commits may use `future! branch-name` for an unmerged dependency.
  Keep dependent work draft and rebase onto the landed base afterward.
- Public pushes, PRs, review requests, comments, closes, and reopens are
  external actions. Local proof never grants publication authority.

## Implementation invariants

Repo-local rules remain authoritative. During review, explicitly check:

- TypeScript types and cleaners at network, disk, bridge, provider, and
  persistence boundaries; optional fields or migrations for stored formats.
- `account.dataStore` instead of `account.localDisklet`; Redux for
  account-global settings; nested merges and cache reset across logout/login.
- Shared themed React primitives, functional components, `useHandler`,
  accessibility, safe areas, loading/failure/disabled states, localization, and
  rapid-repeat protection.
- Original errors/stacks, awaited sequencing, silent cancellation, concurrency
  guards, and cleanup of timers/background tasks.
- Token IDs versus currency codes; `null` native-asset semantics; integer native
  amounts; `biggystring` arithmetic; explicit min/max rounding tests.
- No unguarded sensitive logging or client-embedded secret presented as a
  security boundary.

## Setup and validation

For `edge-react-gui`, current metadata wins. The August 2026 baseline uses npm:

- After an explicitly approved install, `npm ci` uses the lockfile and
  `npm run prepare` runs the scripts disabled by `.npmrc`.
- Detect scripts first; do not assume `npm run tsc` exists.
- Prefer repo-pinned binaries. Do not let bare `npx` silently download a missing
  tool; report the gap or use the verified local binary.
- Start with focused Jest/React Native Testing Library coverage, then touched
  lint, formatter, type checks, `git diff --check`, and the generic Pre-Push
  Regression Gate.
- Use `npm run verify` or `npm run precommit` when practical and authorized;
  name exact blockers rather than inventing substitute success.
- String changes search existing keys and run `npm run localize`.
- Visual GUI changes need actual iOS, Android, small-screen, and large-screen or
  tablet coverage, or an explicit unproven matrix. Check localization expansion,
  keyboard, safe areas, loading, failure, disabled, cancellation, and double tap.
- Maestro YAML edits are not device proof; report platform, device, flow, and
  actual execution.
- Currency/provider work covers native and token cases, regions/payment types,
  min/max and rounding, cancellation, timeout, failure, unit tests, authorized
  network tests, and the built bundle in the GUI.
- Never use real funds, production signing, or production credentials merely to
  close a proof gap.

Installs, CocoaPods, Gradle repair, native toolchain changes, and dependency
upgrades still require the reviewer's explicit local-mutation approval.

## Pull request contract

Preserve the current PR template. For GUI work, expect:

- CHANGELOG decision and dependency PRs;
- problem, root cause, user-visible behavior, and scope boundaries;
- exact commands/results and known unproven gates;
- screenshots/recordings and iOS/Android/device matrix for visual work;
- limitations and intentionally deferred work.

Ideas and local prototypes do not need prior product-owner approval. A
user-authorized public draft may present alternatives and request a decision.
Before a public non-draft PR treats a new API or product surface as selected,
record the maintainer/product decision. A green prototype proves feasibility,
not product selection.

Preserve the repository PR template, then add the smallest useful proof appendix
from templates/edge-app-proof-packet.md. Keep full local logs private; publish
only reviewer-useful, reproducible, sanitized evidence.

## Secrets, attestation, and releases

- Never publish `env.json`, API/provider secrets, seeds, private keys, tokens,
  signing/store credentials, SSH keys, release Firebase files, or sensitive PII.
- Attestation spans GUI native/TypeScript code and `edge-info-server`; inspect
  both sides plus platform lifecycle and rate-limit behavior.
- Deploy, signing, version-allocation, Fastlane, keystore, store-upload, revoke,
  renew, publish, and production actions require explicit release authority and
  validated configuration. A successful build grants none of that authority.

## Bookkeeping and done

- Track Edge lanes in `~/projects/CONTRIBUTIONS_INDEX.md` and preserve
  registered canonical paths.
- Keep initiative findings in their owning `STATUS.md`, `FINDINGS.md`, roadmap,
  and append-only `LOG.md`.
- Record public/private provenance boundaries without copying sensitive source
  text into public artifacts.
- End public issue/PR status with its full URL.

Done means repo and base are confirmed, contract gates are satisfied, the diff
is narrow, the Edge proof state is satisfied or honestly not_required, required
proof is accurately reported, private evidence stayed private, public actions
were authorized, and ledgers match reality.

Source snapshot SHA-256:
`2ab7852534d1da8739dcaac77a8bd3564f429df97f18deda29907f1298ab8daa`.
