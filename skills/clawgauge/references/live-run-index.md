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
