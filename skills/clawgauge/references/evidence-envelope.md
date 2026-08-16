# ClawGauge Evidence Envelope v1

ClawGauge compares clawgauge.evidence.v1 envelopes, not naked ShellBench JSON.
The embedded benchmark_result is the unmodified classic
shellbench.BenchmarkResult. ClawGauge-owned claims live only under provenance;
they are not upstream ShellBench fields.

## Build or validate

Build from a raw result plus an independently assembled attestation:

    python3 scripts/build_evidence_envelope.py raw-result.json \
      --attestation attestation.json --out evidence.json

Validate an existing envelope by omitting --attestation:

    python3 scripts/build_evidence_envelope.py evidence.json >/dev/null

The importer hashes canonicalized benchmark_result content. It fails closed
when provenance is incomplete or the embedded result no longer matches its
hash. It never copies a local input path into the artifact.

## Required provenance

An attestation is either the provenance object itself or an object containing
that key. Version 1 requires:

- exact OpenClaw and ShellBench commits;
- host class;
- campaign ID, start/end window, concurrency, model order, retry policy, and
  exclusion policy;
- environment and task-snapshot fingerprints, adapter, prompt variant, harness
  profile, and tool-profile fingerprint;
- requested and observed provider/model/reasoning/fast state for the candidate route.
  Requested fast is the tri-state unset/on/off; observed fast is the effective
  boolean. Unset may resolve to either boolean, while explicit on/off must match;
  compared envelopes must share both the requested state and the observed
  effective boolean;
  verified identity and reasoning proofs, explicit fallback_used false, and a
  proof supporting fallback absence;
- requested and observed provider/model/reasoning for the judge, whether it
  affects scoring, and verified identity and reasoning proofs;
- when cost/value is used: pricing date, currency, source, and exact numeric
  input, cached-input, output, and reasoning rates;
- pinned release ID, exact sorted-task-ID fingerprint, full release task count,
  and complete true.

Each proof is an object with non-empty kind and reference strings. A boolean
alone is not evidence. References should be stable artifact IDs or
content-addressed records, never secrets or absolute local paths.

The task fingerprint is:

    sha256(UTF8(join(sort(task_ids), "\n") + "\n"))

Core-19 is reported only when the upstream release ID is clawbench-core-v1, the
attested and observed count is exactly 19, and the task-ID fingerprint verifies.
The pinned Core-19 fingerprint is
sha256:5c19c73824478c6890b46e09fe74530ed393991e0ea02a83fe973fdba24509ea.
Any other verified release is labeled by its pinned release ID. A count of 19
alone proves nothing. A declared subset is valid when `complete` is false,
the full release count is larger than the observed set, and the observed task
fingerprint verifies.

## Comparison rules

The comparator blocks on missing provenance or protocol drift. Two runs are
never directional: one run is a routing smoke and two runs are insufficient
repeats. Directional evidence begins at three runs per task.

Cost fields become n/a when pricing provenance is unavailable; capability
comparison remains valid. Missing
failure-mode evidence is n/a; an explicit empty count map means no failures were
recorded.

The value objective requires all three lane floors:

    --min-score 0.70 --min-reliability 0.80 --min-worst-of-n 0.55

--require-pass-hat-k optionally requires overall_pass_hat_k equal to 1. With no
complete floor set, the value read is unavailable-floor. If neither route
passes, it is no-eligible-route; price never rescues an incapable route.
