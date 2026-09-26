# Run Evidence

The current workflow and public package contain sanitized synthetic fixtures
only. A live local skill may retain historical artifacts under `examples/runs/`
or `runs/` from earlier revisions; treat those as archival, machine-specific
evidence, not a current baseline or distributable package.

New runs belong under `skills/clawgauge/runs/<run-id>/` on the evaluating
machine and should preserve:

- the frozen decision and run manifest
- untouched native ShellBench artifacts
- ClawGauge v2 envelopes, including cache kind/config/lifecycle/hits and downstream route proofs
- QA summaries, `qa-evidence.json`, and every attempt sidecar
- character summaries, transcript hashes, and judge attestations
- comparison JSON/Markdown and the final lane decision

Publish only deliberately scrubbed evidence. The public mirror excludes both
historical run directories. Historical VPS paths and former compatibility
symlinks are not part of the current Mac workflow.

## Current contained campaign

`20260926T0453-clawosseum-sol6-grok47/` is the first host-contained
any-authorized-chat campaign. The internal runner component was Clawosseum; the
campaign and all evidence belong to ClawGauge.

- 18/18 serial cells completed in 18 fresh SSH-sandbox workspaces.
- Exact routes and zero fallback were observed for every cell.
- `xai/grok-4.7`: `9/9`.
- `openai/gpt-6-sol`: `8/9`.
- Containment proof, manifest, result, summary, and per-cell receipts are all in
  that run directory.
