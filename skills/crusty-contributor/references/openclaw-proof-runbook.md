# OpenClaw Proof Creation Runbook

Use this when contributing to `openclaw/openclaw` or a close OpenClaw ecosystem repo and proof can affect review, labels, mergeability, or maintainer confidence.

This runbook exists because OpenClaw proof is not one checkbox. A PR can have evidence in the body, pass a proof workflow, and still fail ClawSweeper/Mantis/maintainer acceptance for the current head. A PR can also have `proof: sufficient` and still need author work for CI, conflicts, duplicate/canonical-path decisions, or a real functional finding.

## Source Of Truth

Check these before making proof claims:

- target repo `AGENTS.md`, `CLAUDE.md`, and `CONTRIBUTING.md`
- `scripts/github/real-behavior-proof-policy.mjs` in the target repo
- `scripts/sync-openclaw-label-colors.mjs` plus live `gh label list --repo openclaw/openclaw` for exact label spellings
- latest PR labels, latest ClawSweeper/Mantis comments, latest relevant check runs, and current head SHA from GitHub
- local `projects/CONTRIBUTIONS_INDEX.md` only as a cached board; verify live before public action

Relevant OpenClaw guidance captured during this research:

- External PRs are machine-checked for authored `What Problem This Solves` and `Evidence` sections. `Why This Change Was Made` and `User Impact` are current template / maintainer-context sections, but do not treat them as the same machine-enforced gate unless current repo code says so.
- When ClawSweeper, Codex, Barnacle, or a maintainer asks for more context/evidence, edit the PR body instead of only replying in comments.
- User-visible and external API behavior often need live or real-environment proof, not only unit tests.
- Telegram-visible behavior should use Telegram/Desktop proof when feasible.
- PR screenshots/videos/artifacts should be attached through comments or artifact stores, not committed to product branches.
- Full/broad/E2E/cross-OS proof should use Crabbox/Testbox when local proof would be too heavy or too environment-specific.

## The Proof Gates

### 1. PR Body Context Gate

This is the durable human/bot context gate.

The enforced minimum for external OpenClaw PR context is:

- `What Problem This Solves`
- `Evidence`

The current PR template also expects useful context such as:

- `Why This Change Was Made`
- `User Impact`

Use all four when drafting or repairing a PR body, but be precise when diagnosing a bot gate: the machine proof-context check is not the same as the full human-friendly PR template.

`Evidence` should summarize the strongest validation. It can include focused tests, CI results, screenshots, recordings, terminal output, live observations, redacted logs, artifact links, and explicit not-tested gaps.

If a bot or maintainer asks for proof/context, update the PR body first, then leave a short comment pointing to the update or requesting re-review. Do not bury the only proof in a comment thread.

### 2. Real-Behavior Proof / Supplied Evidence Gate

This is the structured proof/workflow/label surface. Labels such as `proof: supplied` or a green `Real behavior proof` check can mean the PR has a proof packet or structured evidence. It does not automatically mean ClawSweeper accepted that evidence as sufficient for merge.

Treat `proof: supplied` as "evidence exists" rather than "done." If the same PR still has `status: 📣 needs proof`, the supplied proof did not satisfy the bot/reviewer.

### 3. ClawSweeper/Mantis/Maintainer Acceptance Gate

This is the proof-readiness gate.

Look for labels and comments such as:

- `proof: sufficient`
- `proof: 📸 screenshot`
- `proof: 🎥 video`
- `status: 👀 ready for maintainer look`
- `status: 🚀 automerge armed`
- `clawsweeper:merge-ready`
- `clawsweeper:automerge`
- ClawSweeper review text saying proof is sufficient and the result is ready for maintainer review
- Mantis comments/artifacts that actually show the expected user-visible behavior

ClawSweeper's policy code models exact-head acceptance: trusted proof verdicts are tied to a PR number and the current 40-character head SHA. That marker is machine-facing and may not be obvious in the human-visible comment excerpt; humans usually rely on labels and visible review text. Operationally, any rebase, amend, or force-push should trigger a fresh proof review ritual. Do not cite stale proof as current unless you also prove the code path and head relationship still make it valid.

### 4. Non-Proof Merge Gates

Proof can be sufficient while the PR is still not merge-ready. Always check for:

- `status: ⏳ waiting on author`
- `status: 🛠️ actively grinding`
- `status: 🔁 re-review loop`
- `clawsweeper:human-review`
- `clawsweeper:needs-security-review`
- `clawsweeper:needs-live-repro`
- `clawsweeper:needs-maintainer-review`
- `clawsweeper:needs-product-decision`
- merge conflicts
- branch-caused red CI
- persistent data-model / migration / upgrade-compatibility risk
- duplicate or superseded PRs where another canonical branch is the real landing path
- maintainer/security/product pauses even after proof is accepted

Do not say "merge-ready" when any of these remain. Say exactly which gate remains.

## Fresh-Head Rule

Run this after every rebase, amend, merge-from-main, force-push, generated artifact refresh, or meaningful proof update.

1. Capture current head:
   - `git rev-parse HEAD`
   - `gh pr view <PR> --repo openclaw/openclaw --json headRefOid,mergeable,labels,statusCheckRollup,updatedAt`
2. Re-run the minimum proof set for the touched surface.
3. Update the PR body `Evidence` section with current-head validation.
4. If using live proof, make the artifact/comment say which head it applies to.
5. Post a short `@clawsweeper re-review` comment only after the body/proof is current.
6. Re-check labels and latest bot review. Do not call the PR merge-ready until labels/status/comments agree and branch-caused CI/conflicts are resolved or honestly scoped.

Old proof is useful history. It is not fresh proof.

## Choosing The Proof Type

Use the narrowest proof that would convince a skeptical maintainer for the changed behavior.

### Docs-only or copy-only PR

Usually enough:

- `git diff --check`
- relevant docs/render/link sanity when practical
- clear PR body Evidence explaining the doc path and why no runtime proof applies

Add screenshots only when the docs change rendered UI/visual behavior.

### Pure unit-level behavior

Usually enough:

- focused tests near the touched code
- negative regression for the closest near-miss
- sibling parity notes if the change affects routing, auth, parsing, command detection, or metadata
- local formatter/lint/type gates for touched files

If ClawSweeper asks for real behavior anyway, do not argue from tests alone. Add the smallest real scenario proof or explain exactly why it is not possible.

### Pure UI / visual formatting behavior

Usually enough:

- focused formatter/component tests when possible
- before/after screenshots or exact before/after values
- a short explanation of why no live channel/runtime proof applies

Good example: #95485 proved a compact token formatter by showing the before-fix value `999950: 1000k` and after-fix value `999950: 1M`, with `proof: sufficient`, `proof: 📸 screenshot`, and ready labels.

### Channel-visible behavior

Examples: Telegram, SMS, Slack, Discord, TTS/media delivery, message routing, command menus, reply context.

Expected proof:

- focused code tests for the changed handler/runtime path
- at least one real or realistic transport proof for the user-visible path
- screenshots, transcript snippets, message IDs, artifact links, or redacted logs
- negative proof that the closest wrong route/suppression/duplicate does not happen

For Telegram-visible behavior, prefer Mantis/Telegram Desktop proof when the PR has `mantis: telegram-visible-proof` or when ClawSweeper/maintainers expect visual proof. If Mantis does not run, is not authorized, or fails to capture the expected behavior, document that and provide alternate proof rather than pretending the request itself is proof.

### Config, startup, upgrade, session, provider, or node-host behavior

Expected proof is often broader than a unit test:

- isolated install/update/start/restart scenario when the bug is lifecycle-dependent
- Crabbox/Testbox for full/broad/cross-OS proof
- exact config before/after, with secrets redacted
- current/shipped behavior comparison when the PR changes compatibility, defaults, or fallbacks
- migration/upgrade compatibility proof when persistent serialized state or config schema changes
- clear statement of operator action required, if any

### Security, auth, secrets, privacy, or output-redaction behavior

Expected proof:

- positive path showing intended access or redaction works
- negative path showing unauthorized/leaky near-miss does not work
- no secret/private data in PR body, comments, screenshots, logs, or artifacts
- dependency/source contract proof when the behavior relies on external tools or APIs
- maintainer/security review may still be required even with `proof: sufficient`

### External API or provider behavior

Expected proof:

- official docs/source/types checked for current behavior
- live smoke test when feasible
- redacted request/response evidence
- explicit note when the live smoke used installed OpenClaw instead of the PR branch, and what branch-specific behavior remains covered by tests

## Fresh Proof Packet

Before public re-review, assemble this packet in local notes and then put the durable version in the PR body or a concise comment plus body update.

Required fields:

- PR number and current head SHA
- base/main SHA or date if relevant
- changed surface and risk class
- problem statement in user/product terms
- positive proof: intended behavior after the patch
- negative proof: closest near-miss still behaves correctly
- focused tests and commands run
- live/real-environment proof with artifact links when required
- not-tested or blocked proof, stated plainly
- CI state: branch-caused failures, unrelated main/infra failures, queued checks, merge conflicts
- non-proof gates: author-wait, maintainer/security/product review, duplicate/canonical path, migration/compatibility concerns
- re-review request only after the above is current

Short comment shape:

```markdown
Updated proof for current head `<sha>`.

Evidence in PR body now covers:
- focused tests: `<commands>`
- live proof: `<artifact/comment/link>`
- negative path: `<what did not happen>`
- known gaps/gates: `<none or exact gap>`

@clawsweeper re-review
```

For shell-heavy comments, write the body to a temp file and use `gh pr comment --body-file` so backticks and `$` do not get mangled.

## Mantis / Telegram Visible Proof Checklist

Use when the changed behavior is visible in Telegram or when a PR carries/needs `mantis: telegram-visible-proof`.

Before requesting Mantis:

- confirm the current head SHA
- write the expected visible behavior in plain language
- define the exact trigger message/callback/action
- define what screenshot, GIF, video, or transcript should prove success
- define the negative behavior that must not appear, such as duplicate fallback text, missing acknowledgement, wrong chat/thread, private text leak, or stale session route

When requesting proof:

- mention the PR and current head SHA
- ask for the specific scenario, not just "proof"
- if the workflow requires maintainer authorization and your comment does not start a run, note that and use another proof path or ask for maintainer help

After Mantis:

- inspect the artifact/comment, not only the fact that a workflow ran
- verify it shows the expected behavior
- if it misses the expected acknowledgement or captures the wrong scenario, treat the proof as insufficient
- update PR body Evidence with the artifact link and observed result

## Label Decoder

Use labels as signals, not as the only source of truth. Exact spellings can evolve; verify with live `gh label list --repo openclaw/openclaw` and repo label scripts before making a public claim.

Common proof labels:

- `proof: supplied`: evidence exists; not necessarily accepted.
- `proof: sufficient`: ClawSweeper considers proof enough for its proof gate, subject to current head and current review state.
- `proof: 📸 screenshot`: screenshot/visual proof is present or recognized.
- `proof: 🎥 video`: video/recording proof is present or recognized.
- `proof: override`: maintainer override for the external PR real-behavior proof gate.
- `mantis: telegram-visible-proof`: Telegram visible proof is expected or relevant.
- `mantis: discord-visible-proof`: Discord visible proof is expected or relevant.

Common status/rating labels:

- `status: 📣 needs proof`: do not call proof-ready. Add or repair proof.
- `status: ⏳ waiting on author`: do not call merge-ready. There is an author-facing change, explanation, or proof task.
- `status: 👀 ready for maintainer look`: contributor-facing proof/change gates are likely clear, but CI/conflicts/security review may still matter.
- `status: 🚀 automerge armed`: automation lane is armed; still watch for required-check, security, maintainer-pause, or current-head churn.
- `status: 🔁 re-review loop`: re-review was requested; wait for/inspect the next result.
- `status: 🛠️ actively grinding`: author has acted and work remains.
- `rating: 🦞 diamond lobster`: very strong readiness signal, not a merge command.
- `rating: 🐚 platinum hermit`, `rating: 🦐 gold shrimp`, `rating: 🦪 silver shellfish`, `rating: 🧂 unranked krab`: decreasing readiness signals. Read the review text; do not infer the blocker from the emoji alone.

Common ClawSweeper gate labels:

- `clawsweeper:automerge`: maintainer opted the PR into bounded ClawSweeper-reviewed automerge.
- `clawsweeper:merge-ready`: ClawSweeper found the PR merge-ready but a human gate is still closed.
- `clawsweeper:human-review`: maintainer review is needed before ClawSweeper can continue.
- `clawsweeper:needs-security-review`: security-sensitive review is needed.
- `clawsweeper:needs-live-repro`: live local, Crabbox, or manual validation is needed.
- `clawsweeper:needs-maintainer-review`: maintainer review is needed before automation.
- `clawsweeper:needs-product-decision`: product/behavior decision is needed.
- `clawsweeper:needs-info`: more reporter information is needed.
- `clawsweeper:current-main-repro`, `clawsweeper:source-repro`, `clawsweeper:not-repro-on-main`: reproduction state labels; useful for issue/PR triage.

Other GitHub fields:

- `mergeable: CONFLICTING`: proof does not matter until the branch is rebased/resolved.
- red status checks: decide whether branch-caused, upstream/main, infra, or flaky; fix only branch-caused failures.

## Example Patterns From OpenClaw PRs

The examples below intentionally mix community PRs and Sean/JPop PRs. Community examples are first so the runbook follows repo norms rather than only our own scars.

### Good: #94612 macOS NSOpenPanel for embedded Control UI file inputs

Why it worked:

- Non-Telegram visual proof showed the after-fix real app path, not only unit tests.
- ClawSweeper compared sibling/overlap PRs and identified this as the stronger canonical candidate because it covered Dashboard and Canvas surfaces.
- The PR reached automerge and merged.

Pattern to copy: for UI/app behavior, provide real before/after visual proof and explain sibling coverage when competing PRs exist.

### Good: #94118 Telegram rich local Markdown link hrefs

Why it worked:

- Mantis captured native Telegram Desktop before/after screenshots/GIFs.
- ClawSweeper called out live proof and send-path coverage.
- The evidence tied the visual artifact to the reported user-visible link rendering failure.

Pattern to copy: for Telegram rendering/delivery behavior, use Mantis artifacts that show baseline and candidate behavior, then link them in the PR body.

### Good: #93002 Telegram progress draft cleanup before tool output

Why it worked:

- Focused ordering tests plus Mantis Telegram Desktop before/after GIFs proved the exact progress-draft behavior.
- The author updated the PR body with the Mantis proof link before re-review.
- ClawSweeper rated proof strongly and marked it ready for maintainer review.

Pattern to copy: combine code-path tests with visible channel proof for ordering/delivery bugs.

### Good: #94977 Telegram outbound reaction directives

Why it worked:

- Baseline artifact showed raw reaction directive text leaking in Telegram; candidate artifact showed the expected native reaction behavior.
- ClawSweeper connected the proof to the canonical issue and adjacent distinct issues.

Pattern to copy: prove both the bad current-main user-visible symptom and the after-fix behavior.

### Good: #95485 compact token formatter

Why it worked:

- The surface was a pure UI formatter, so exact before/after value proof plus focused tests was enough.
- Screenshot/visual evidence showed `999950: 1000k` becoming `999950: 1M`.

Pattern to copy: choose proof proportional to the surface. Not every fix needs a live channel run.

### Good: #95472 session abort controllers and #95432 multi-message streaming

Why they worked:

- ClawSweeper accepted focused runtime/core-pipeline proof and explicitly treated live Telegram replay as optional or a maintainer decision.
- The proof matched the narrow boundary under review instead of overbuilding a broad demo.

Pattern to copy: "real behavior" can be a focused runtime probe when it exercises the real boundary. Live transport proof is strongest for channel/UI uncertainty, not mandatory for every session-state fix.

### Negative: #92945 Telegram stale command hash

What failed:

- The PR had `proof: supplied`, `proof: 🎥 video`, and Mantis proof requests, but still had `status: 📣 needs proof`.
- Comments showed refreshed heads and repeated proof requests; the proof did not clear the current review gate.

Lesson: video/proof labels do not clear the proof gate by themselves. The artifact must prove the expected behavior for the current head.

### Negative: #94926 Telegram renderMode config

What failed:

- Mantis captured screenshots, but ClawSweeper still found the config surface incomplete/unproven.
- The proof did not establish the full compatibility/config/docs/setup surface for the proposed mode.

Lesson: screenshots can prove a visual symptom while leaving config/compatibility proof incomplete.

### Negative: #95396 safe restart wait=0

What failed:

- Proof was sufficient, but the PR still had `status: ⏳ waiting on author`.
- ClawSweeper still required review/fix follow-through before merge.

Lesson: proof sufficiency is not merge-readiness.

### Negative: #95484 compaction successor transcript

What failed:

- Proof was strong, but ClawSweeper called out persistent data-model change and migration/upgrade compatibility proof.

Lesson: persistent state/config migrations need upgrade-compatibility proof beyond behavior tests.

### Negative: #95468 Workboard archived cards

What failed:

- The PR had proof-positive signals, but ClawSweeper recommended a different older PR as the canonical landing path.

Lesson: proof-positive does not mean this branch should land. Redundancy/canonical-path checks still matter.

### Sean/JPop Reference: #90998 Native SMS text slash-command auth

Why it worked:

- PR had focused module tests for command authorization and negative inline slash-token behavior.
- Evidence distinguished branch-specific command-context proof from optional live transport proof.
- Live proof showed real Twilio/Gateway/carrier `/status` and `/new` style traffic with private data redacted.
- The proof comment was honest that the live smoke used installed OpenClaw, while branch-specific behavior remained covered by tests.

Pattern to copy: combine focused tests for branch-specific code with a scoped live transport proof, and explicitly state the boundary between them.

### Sean/JPop Reference: #51762, #93218, and #85543 recurring blockers

What they teach:

- #51762: local focused tests did not replace end-to-end config/startup/lifecycle proof.
- #93218: a Mantis request/artifact did not prove the expected `/stream` acknowledgement, so proof remained insufficient.
- #85543: proof sufficiency could not override an unresolved functional predicate finding.

Pattern to copy: report the exact remaining gate instead of compressing everything into "needs proof."

## Anti-Patterns

Avoid these:

- saying "proof is done" because `proof: supplied` exists while `status: 📣 needs proof` remains
- reposting `@clawsweeper re-review` without changing PR body/proof
- relying on proof from an old head after rebase/amend/force-push
- using local tests as the only proof for a live channel/UI/lifecycle bug
- treating a Mantis request as proof without inspecting what Mantis captured
- treating screenshot/video labels as enough when the underlying config/session/security/migration surface remains unproven
- posting private chat metadata, phone numbers, tokens, local hostnames, or personal memory in proof artifacts
- committing proof images/videos/logs to the product branch
- calling a PR merge-ready when it is merge-conflicting, has branch-caused red CI, has `status: ⏳ waiting on author`, needs maintainer/security/product review, or is superseded by a stronger canonical PR

## Done Definition For OpenClaw Proof

You may say proof is ready only when all are true:

- PR body has current `What Problem This Solves` and `Evidence`
- evidence names the current head SHA or is clearly refreshed for it
- proof type matches the changed surface
- focused positive and negative tests/proof are present
- live/Mantis/Crabbox/Testbox proof exists when the changed behavior needs it
- known gaps are stated plainly
- latest labels/comments no longer ask for proof or author action
- branch-caused CI is green or honestly repaired/queued
- merge conflicts are resolved
- maintainer/security/product/canonical-path gates are either clear or explicitly named as still pending

If any item fails, report the exact missing proof or blocker instead of using merge-ready language.