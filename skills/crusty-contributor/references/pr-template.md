# PR Body Template

Use this as a starting point. Insert the Merge Brief above the target repo's
existing template and preserve every required heading exactly. The brief
supplements, never replaces, repository-required sections.

## Merge Brief

<!-- Keep this first and scannable in roughly ten lines. A maintainer should be
able to understand why this deserves attention and what decision remains in
under one minute. Use "None" rather than omitting an applicable field. -->

**Problem:** <!-- User-visible pain or concrete behavior gap. -->

**Why now:** <!-- Strongest honest demand signal; distinguish independent demand,
self-reproduction, accepted direction, operational impact, or vendor/standards pressure. -->

**Value:** <!-- Who benefits and what becomes better if this lands. -->

**Fix:** <!-- Smallest complete solution in plain language. -->

**Scope:** <!-- Diff size/file count, main file groups, and why any excess is atomic. -->

**Risk:** <!-- Main regression risk and its mitigation. -->

**Proof:** <!-- Exact focused tests and real-behavior evidence; link deep receipts below. -->

**Non-goals:** <!-- Explicitly excluded behavior or follow-up work. -->

**Maintainer ask:** <!-- One concrete decision or action: review, accept contract, test, merge. -->

<!-- Put detailed root-cause analysis, logs, matrices, and forensic receipts below
this brief or in collapsed/linkable artifacts. Do not make reviewers excavate the pitch. -->

## Summary

<!-- One short paragraph: what changed, in plain public-safe language. -->

## Motivation

<!-- Why this matters to users/maintainers. Link related issue(s). -->

Closes #<!-- issue number, or remove this line -->

## Root Cause

<!-- For fixes: what caused the bug. Remove if not relevant. -->

## Changes

- <!-- One bullet per logical change. -->

## Non-goals / Scope Boundaries

- <!-- What this intentionally does not change. -->

## Maintainer Fit

<!-- Briefly note nearby conventions followed, relevant prior issue/PR history checked, and why this is robust rather than a fragile workaround. Remove if overkill for a tiny PR. -->

## Testing

- [ ] <!-- command or manual verification -->

## Checklist

- [ ] Read repo-native contributor guidance.
- [ ] Preserved every repository-required heading and passed its body/context validation.
- [ ] Checked nearby conventions and relevant prior PR/issue history for the touched area.
- [ ] Branched from current upstream default branch, not stale fork state.
- [ ] Diff is focused; no unrelated cleanup bundled in.
- [ ] No secrets, private paths, local machine lore, or personal/company context leaked.
- [ ] Tests/docs/changelog updated according to repo conventions.
- [ ] User-facing changes have changelog/docs when required.
- [ ] Root-cause/robustness rationale is clear, or intentionally omitted because this is trivial.
- [ ] CI/review follow-up plan is clear.

## AI Assistance

<!-- Include if expected by repo norms. Example: This PR was prepared with AI assistance and reviewed by the author. -->

## Investigation Trail

<!-- Optional when useful: link or attach a sanitized transcript/summary showing the investigation path and time spent. -->
