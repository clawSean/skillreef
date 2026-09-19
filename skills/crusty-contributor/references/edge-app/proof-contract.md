# EdgeApp Pull Request Proof Contract

Use for every pull request the author/reviewer authors or materially updates in an
EdgeApp-owned repository. This is our contributor standard, not a claim that
Edge currently enforces it organization-wide. Target-repository instructions,
the PR template, security policy, and maintainer direction remain authoritative.

The goal is reviewer confidence with the least evidence that actually proves
the change. This contract forbids green-check theater, stale evidence, hidden
gaps, and broad claims supported by narrow tests.

## Exploration and publication boundary

This contract measures evidence for a candidate; it does not gate product
thinking.

- Suggest, critique, and compare UX, API, architecture, and product options
  freely.
- Build local prototypes freely and label them as candidate designs.
- Use a public draft only when the reviewer authorizes publication and it is a useful
  alignment surface; a draft does not imply owner approval.
- Require owner alignment before a public non-draft PR presents a new public,
  persisted, breaking, security, or release contract as selected.
- Scale exact-head and real-boundary proof with maturity: early candidates may
  remain planned or attempted; proof-complete claims require the full class gate.

## Non-negotiable contract

A PR is proof-complete only when:

1. The repository, target branch, base SHA, full head SHA, owning layer, user
   job, and intended behavior are named.
2. Each user-visible or contract claim maps to specific evidence.
3. The focused regression distinguishes the fixed behavior from the old or
   nearest wrong behavior.
4. The closest meaningful negative, preserved default, or failure path is
   covered.
5. Evidence crosses the real boundary when the claim involves UI, lifecycle,
   persistence, native code, a provider, a server, or another repository.
6. Artifacts were inspected and sanitized; generation or a green workflow alone
   does not count.
7. Skipped platforms, blocked routes, synthetic inputs, forced state, and
   remaining uncertainty are explicit.
8. Proof status is separated from CI, conflicts, security, product, migration,
   release, maintainer, and canonical-contract gates.
9. Exploratory product/API choices are labeled as candidates. Owner alignment
   is required before a public non-draft PR represents a contract as selected;
   tests prove behavior or feasibility, not product selection.
10. No real funds, production signing, production secrets, or private-source
    disclosure is used merely to make the proof look stronger.

## Proof states

Keep one state for the current candidate head:

- not_required: runtime proof does not apply; exact static checks and the reason
  are recorded.
- planned: claim, route, positive case, negative case, and acceptance conditions
  are selected but not executed.
- attempted: a real run occurred, but evidence is incomplete, wrong-state,
  uninspected, or otherwise insufficient.
- satisfied: inspected current-head evidence covers the changed surface and
  nearest meaningful negative.
- blocked_external: a required device, permission, credential, provider, owner
  decision, or authorized route is unavailable.
- stale: the candidate changed after evidence was produced.

Use satisfied or not_required before calling our contribution proof-complete.
A draft may carry planned, attempted, or blocked_external when the exact debt is
visible. Proof-complete never means merge-ready by itself.

## Intake and risk class

Before implementation, record:

- repo, base, candidate head, issue/initiative, author, and intended reviewer;
- user problem, root cause hypothesis, owning layer, scope, and non-goals;
- public/private provenance boundary;
- any contract or product decision needed before non-draft publication, with
  owner and status; otherwise mark the work exploratory;
- one internal risk class:
  - R0: docs, copy, comments, or body-only;
  - R1: pure logic, tests, or internal refactor;
  - R2: user-visible UI, integration, or lifecycle behavior;
  - R3: auth, storage, public API, cross-repo, native, provider, or server policy;
  - R4: funds, identity, signing, secrets, security, migration, or release.

The class chooses the minimum proof; it is not an Edge label.

## Minimum evidence by class

### R0 — docs and copy

- Diff and formatting checks plus current links, render, and repo-required docs
  checks.
- Execute any command or procedure whose correctness the text promises.
- State why runtime proof is not_required.

### R1 — pure logic

- Focused positive regression and nearest negative or preserved-default test.
- Show old failure, a targeted mutation, a golden/reference vector, or explain
  why the test still discriminates.
- Touched type, lint, format, diff, and repository gates.

### R2 — UI, integration, and lifecycle

- R1 evidence plus the actual user-reachable boundary.
- Inspect screenshots or recordings for expected and forbidden states.
- Cover loading, empty, failure, disabled, cancellation, repeat, navigation,
  restart, or background paths that can reach the change.
- Name iOS, Android, device size, locale, Maestro/test-only state, and any
  unproven matrix cells.

### R3 — auth, storage, API, cross-repo, native, provider, or server

- R2 evidence where visible behavior exists.
- Name state ownership and lifetime; cover restart, logout/login, network loss,
  stale local state, cleanup, and second device when relevant.
- For owner/consumer work, run or reason through old/old, old/new, new/old, and
  new/new, using the exact dependency revision.
- For native/provider/server paths, use an authorized real boundary when the
  claim depends on it and report the missing platform or live gate honestly.

### R4 — funds, identity, signing, secrets, security, migration, or release

- R3 evidence plus independent final-diff review or an explicit record that it
  was unavailable.
- Use deterministic vectors, independent verification, unit/rounding/bounds
  cases, unauthorized or leak-path negatives, and compatibility/migration proof
  appropriate to the change.
- Keep security disclosure private and obtain the relevant owner/release
  authority. A local proof cannot authorize deployment, signing, or spending.

## Claims must be discriminating

- Assert the meaningful event, value, or state—not request count, compilation,
  a proxy flag, or a screenshot from forced setup.
- When practical, run the regression against the prior implementation or a
  focused mutation and record the expected failure.
- If old behavior is intentionally preserved, prove both old default and new
  opt-in behavior.
- Pair whole fixtures with small invariant tests for mappings, amounts,
  perspectives, addresses, signatures, and provider calls.
- A higher-looking test does not replace a precise lower-layer invariant.
- Do not run generic engine/config/app theater when it cannot exercise the
  changed path.

## Artifact and runtime acceptance

Before a runtime run, define the trigger, expected result, forbidden result,
artifact, environment, cleanup, and private-data boundary. Afterward, inspect
the artifact itself.

Reject evidence that is empty, stale, wrong-state, generic status, test-only
when production differs, unrelated to the claim, or privacy-leaking. Label
real, fake, stubbed, forced, synthetic, simulator, device, test-server, and
production inputs exactly.

## Freshness

Any head change sets the packet to stale until reviewed. If a rebase leaves the
relevant blobs, dependencies, generated outputs, and proof environment
identical, the artifact may be explicitly rebound after verifying those facts
and refreshing head/base/CI metadata. Behavior, dependency, fixture, toolchain,
or generated-output changes require the affected proof to rerun.

After every material review round, compare the final diff, reopen unresolved
threads, rerun affected proof, and update the PR narrative. Generated summaries
and automated approvals are advisory and may describe an older head.

## Reviewer packet

Use templates/edge-app-proof-packet.md under the repository's existing PR
template. Keep the public packet concise and reproducible; do not paste raw
logs. The local packet may be richer but must still avoid secret values.

Every packet names:

- exact head/base and risk/state;
- claim, positive proof, negative proof, commands, results, and environment;
- inspected artifacts and redaction;
- compatibility, platform, lifecycle, and provider matrix as applicable;
- known gaps and remaining non-proof gates.

Good completion language: "Proof satisfied on head <sha>; hosted CI and
maintainer review remain." Good blocked language: "Proof attempted; Android
device coverage is blocked_external and remains unproven."

Do not publish "works", "all tests pass", "fully tested", or "merge-ready"
without the exact scope those words describe.

## Completion

The contract is satisfied when the current-head packet is reproducible,
claim-specific, discriminating, inspected, sanitized, honest about gaps, and
paired with a final-diff review. Product, security, release, and maintainer
gates remain separately owned.
