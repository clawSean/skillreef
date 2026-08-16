# Personal Agent QA Profile Pin

Verified against OpenClaw commit
`8277cb24a16ca783c841a3af9bc761fc4103600b`.

Invoke the full pack with:

```bash
pnpm openclaw qa run --qa-profile personal-agent
```

The expected ten scenario IDs are:

1. `personal-reminder-roundtrip`
2. `personal-channel-thread-reply`
3. `personal-memory-preference-recall`
4. `personal-redaction-no-secret-leak`
5. `agent-tool-safety-approvals`
6. `personal-approval-denial-stop`
7. `personal-task-followthrough-status`
8. `personal-share-safe-diagnostics-artifact`
9. `personal-no-fake-progress`
10. `personal-failure-recovery`

ClawGauge freezes this expected set in its run manifest and verifies the
observed set from `qa-suite-summary.json` and `qa-evidence.json`. A missing,
extra, failed, skipped, blocked, or stalled cell prevents a live QA pass.

`qa suite --preflight` is a lower-level bootstrap check. It may prove the
harness works under a mock provider, but it is never a Personal Agent profile
pass and never model-quality evidence.

The taxonomy-resolved profile is authoritative. The same-commit prose table
still names `personal-tool-safety-followthrough`, but that scenario owns only
secondary coverage. `agent-tool-safety-approvals` is the primary owner selected
at runtime for `agent-runtime.tool-safety-controls`.

Repeated or retried attempts remain separate evidence. A later pass does not
erase an earlier failure; exclusions require a declared reason in the campaign
protocol.
