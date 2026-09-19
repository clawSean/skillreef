# Competitive Overlap Defense

Read this whenever an owned upstream PR is open and another issue, PR, or mainline commit may implement the same behavior. The goal is to maximize the quality and mergeability of the upstream result without turf behavior, premature concession, or silent loss of useful provenance.

## 1. Detect the root-cause cluster

Run at PR intake, on each substantive maintenance pass, and whenever a new related issue or PR appears.

Search beyond titles:

- canonical and related issue numbers
- symptom and root-cause phrases
- touched files and exported symbols
- the behavioral invariant or guard being changed
- recently opened, updated, and merged PRs since the last sweep
- recent mainline commits touching the same boundary
- patch or semantic-diff similarity when practical

Classify each candidate as unrelated, adjacent, same root cause, superseding, or already implemented. A credible same-root-cause candidate becomes an immediate merge-risk signal even when both PR titles and linked issues differ.

Automation may discover candidates, but this skill owns the response. Do not describe collision monitoring as live until the collector and alert path have been tested.

## 2. Build a private comparison packet

Keep the ranking private. Record:

- creation and update timeline
- canonical issue and prior patch lineage
- exact files, symbols, and behavior overlap
- implementation differences and compatibility risk
- focused tests and case matrix
- runtime or lifecycle proof, including exact head
- CI, conflicts, review state, assignee, and maintainer signal
- unique evidence each branch contributes

Rank branches by maintainer usefulness, not authorship: correctness, scope, convention fit, proof, currentness, and ease of landing.

## 3. Respond within one monitoring cycle

For a credible collision while both branches are open:

1. Identify the strongest missing evidence or test on our branch.
2. Add that evidence if it is safe, relevant, and can materially improve the candidate.
3. Update our PR body with current-head evidence and related-work links.
4. Cross-link the root-cause cluster once when doing so adds facts, proof, or provenance.
5. Request re-review on our PR only after its body and evidence are current.
6. Rebase only for conflicts, stale-risk, or an explicit request; do not churn the head merely to signal activity.

Do not maintain a branch for ego or commit count. If another branch has already landed or maintainers clearly selected it, freeze ours and report the outcome; the reviewer decides closure.

## 4. Use the narrowest sufficient proof

Start at the changed ownership boundary. Do not require credentialed end-to-end delivery when the uncertainty is entirely inside an unchanged transport boundary.

### Exact-hook or runtime-boundary changes

A production-hook invocation can be real-behavior proof when it exercises the actual changed hook on the exact head. Cover the risks that exist, usually including:

- the failing input before and corrected output after
- ordinary pass-through behavior
- the closest structured or markup variant
- a literal, escaped, or fenced false-positive guard
- empty, trace-only, or all-removed output
- downstream suppression or validation when empty output has meaning

Five cases are not a ritual. The case set is sufficient when it covers the positive path and the nearest ways the fix could corrupt, leak, or misroute output.

### Config, doctor, startup, update, or migration changes

When the bug manifests in a published release or beta, use that affected build as the baseline if repo guidance and safety permissions allow. Run in disposable isolated state with synthetic or redacted config; never mutate the live OpenClaw installation or real user state.

Prefer a same-input before/after packet:

- affected published build reproduces the exact failure
- candidate exact head no longer fails
- resulting config validates
- unsafe or unsupported fields were not written
- a representative unaffected bundled path still works
- unrelated queued work proceeds only when that is part of the claim

Published-beta or provider-specific evidence is guidance about the failing lifecycle, not a universal requirement. It strengthens the candidate when it matches the reported environment. Install, upgrade, credential, private-account, restart, and spend approvals remain independent gates.

## 5. Public overlap language

Public comments must be additive and neutral. Never write that another open branch is stronger, canonical, preferable, or should win before maintainers select it. Never ask a bot to award a winner.

Comment only when at least one is true:

- a missing prior issue or PR should be linked
- the branches touch the same root cause but duplicate analysis missed it
- one branch has unique tests or proof the landing branch should absorb
- real code authorship or operational/security provenance would otherwise be lost

Prefer updating our PR body or the canonical issue first. Comment on the other PR only when the cross-link will materially help triage before merge. Post once; do not campaign.

Template:

> Possible overlap for triage: `<our PR>` and this PR appear to address the same root cause in `<file/symbol>`, linked to `<canonical issue>`.
>
> The evidence looks complementary: `<our PR>` covers `<our distinct proof>`, while this PR adds `<their distinct proof>`.
>
> Suggest treating them as one root-cause cluster and landing whichever branch maintainers prefer. Happy to consolidate any missing test or proof onto the preferred candidate.

After adding the links and proof delta, request ClawSweeper re-review on our PR when authorized and useful. Supply the cluster facts; do not tell the bot which contributor deserves selection.

## 6. Preserve provenance without score-settling

Distinguish:

- original code authorship
- revival or rebase work
- independent implementation
- issue triage and reproduction
- proof and test contributions

Preserve commit authorship or co-authorship only when actual code lineage supports it. For independent convergence, do not imply copying. Record revival, proof, and triage contributions in the local contribution ledger even if another implementation lands.

After merge, add a public lineage comment only when missing provenance affects operations, security, legal attribution, or future maintenance. Do not reopen a settled thread merely to collect contributor credit.

## Done

The overlap is handled only when the root-cause cluster is recorded, our current-head proof gap is either closed or explicitly declined, any useful cross-link is posted once, the selected/frozen state is correct, and the local contribution ledger preserves the factual lineage.