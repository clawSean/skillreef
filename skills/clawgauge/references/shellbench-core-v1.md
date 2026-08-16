# ShellBench Core v1 Pin

Verified against `openclaw/shellbench` commit
`884dd1bb55112c93292e1633081d62504ba49905`,
`tasks-public/MANIFEST.yaml`.

- Release: `clawbench-core-v1`
- Benchmark version: `0.4.0.dev1`
- Release date: 2026-04-20
- Task count: 19

## Standard Mac directional subset

Use this nine-task, n=3 subset for a balanced local route comparison after r0
qualification. It deliberately includes deterministic coding and repo work:

1. `t1-bugfix-discount`
2. `t1-fs-quick-note`
3. `t2-add-tests-normalizer`
4. `t2-config-loader`
5. `t2-priv-redact-doc`
6. `t3-web-research-and-cite`
7. `t4-cross-repo-migration`
8. `t4-delegation-repair`
9. `t4-browser-research-and-code`

Use a smaller subset only for budgeted screening and label its reduced
coverage. Coding-lane claims require both coding tasks plus at least one repo
task.

For the strongest compact coding/repo proof, use `t2-config-loader`: its pinned
asset pack is `t2_config_loader`, deterministic completion runs `pytest -q`,
and trajectory expects read/edit/execute, at least two distinct reads before
editing, self-verification, and recovery. Pair it with
`t1-bugfix-discount` (bugfix + pytest) and `t2-add-tests-normalizer`
(test-authoring plus `verify_added_tests.py`).

## Exact Core-19 task IDs

- `t1-bugfix-discount`
- `t1-fs-quick-note`
- `t2-add-tests-normalizer`
- `t2-browser-form-fix`
- `t2-config-loader`
- `t2-fs-find-that-thing`
- `t2-msg-summarize-thread`
- `t2-priv-redact-doc`
- `t3-data-pipeline-report`
- `t3-data-sql-query`
- `t3-feature-export`
- `t3-msg-inbox-triage`
- `t3-web-research-and-cite`
- `t4-browser-research-and-code`
- `t4-cross-repo-migration`
- `t4-delegation-repair`
- `t4-life-trip-plan`
- `t4-memory-recall-continuation`
- `t5-hallucination-resistant-evidence`

Do not infer Core-19 from “19 tasks.” Verify this exact task set, pinned
release, commit, and task fingerprint in the evidence envelope.

## Caveats

- `t4-memory-recall-continuation` penalizes conversational answers when the
  verifier expects a file artifact; comparisons remain internally fair, but
  absolute capability is understated.
- `t5-hallucination-resistant-evidence` has reported cross-model SNR around
  0.25. Report it as a trust canary and do not use it to rank routes.
- Publication research uses the upstream native campaign runbook and combined
  suite, not a hard-coded Core-19-only campaign.
