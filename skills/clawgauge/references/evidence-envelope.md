# ClawGauge Evidence Envelope v2

ClawGauge compares `clawgauge.evidence.v2` envelopes, not naked ShellBench JSON.
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
that key. Version 2 requires:

- exact OpenClaw and ShellBench commits;
- host class;
- campaign ID, start/end window, concurrency, model order, retry policy, and
  exclusion policy;
- environment and task-snapshot fingerprints, adapter, prompt variant, harness
  profile, tool-profile fingerprint, and complete cache provenance;
- requested and observed provider/model/reasoning/fast state plus direct/router/mixed mode for the candidate route.
  Requested fast is the tri-state unset/on/off; observed fast is the effective
  boolean. Unset may resolve to either boolean, while explicit on/off must match;
  compared envelopes must share both the requested state and the observed
  effective boolean;
  verified identity and reasoning proofs, explicit fallback_used false, and a
  proof supporting fallback absence;
- router/mixed routes: complete downstream observations with provider/model,
  cache-config fingerprint, explicit fallback false, identity/cache/fallback
  proofs, and a coverage proof; mixed requires at least two distinct identities;
- requested and observed provider/model/reasoning for the judge, whether it
  affects scoring, and verified identity and reasoning proofs;
- when cost/value is used: pricing date, currency, source, and exact numeric
  input, cached-input, output, and reasoning rates;
- pinned release ID, exact sorted-task-ID fingerprint, full release task count,
  and complete true.

Each proof is an object with non-empty kind and reference strings. A boolean
alone is not evidence. References should be stable artifact IDs or
content-addressed records, never secrets or absolute local paths.

## Cache provenance

`provenance.cache` has five required blocks:

```json
{
  "runtime": {
    "visibility": "known",
    "kind": "prefix-kv",
    "name": "mlx-vlm",
    "version": "0.6.13",
    "engine": "automatic-prefix-cache"
  },
  "configuration": {
    "enabled": true,
    "persistence": "process-memory",
    "capacity": {
      "visibility": "known",
      "limits": {"blocks": 2048, "block_size_tokens": 16}
    },
    "fingerprint": "sha256:...",
    "proof": {"kind": "runtime-config", "reference": "artifact://..."}
  },
  "protocol": {
    "profile": "controlled-cold-then-warm",
    "reset_between_task_repetitions": true,
    "within_task_reuse": true,
    "cross_task_reuse": false
  },
  "lifecycle": {
    "server_scope": "task-repetition",
    "reset_mechanism": "fresh-process",
    "reuse_scope": "within-task",
    "stability_verified": true,
    "stability_proof": {"kind": "run-manifest", "reference": "artifact://..."}
  },
  "observed": {
    "configuration_fingerprint": "sha256:...",
    "request_count": 18,
    "cold_request_count": 6,
    "warm_request_count": 12,
    "hit_status": "observed",
    "hit_request_count": 12,
    "reused_input_tokens": 48000,
    "hit_metric": "cache_n",
    "cold_latency_ms": {"p50": 3400, "p95": 6100},
    "warm_latency_ms": {"p50": 700, "p95": 1200},
    "hit_proof": {"kind": "request-telemetry", "reference": "artifact://..."}
  }
}
```

The configuration fingerprint is the canonical digest of runtime visibility,
kind, name, version, engine, enabled state, persistence, and capacity visibility and
limits. Proof references are excluded from the digest.

Cache kind is mandatory: `prefix-kv`, `residency-only`,
`full-response-memoization`, `embedding-result`, or
`opaque-provider-managed`. Opaque runtime visibility requires the opaque kind
and proof. Residency-only may not claim request hits or reused input tokens;
embedding-result may not claim reused model-input tokens. Repeated agent
quality/trust trials fail closed when full-response memoization is enabled or a
full-response hit is observed; disabled/no-hit memoization may be attested.

Allowed profiles are `route-native`, `controlled-cold-then-warm`, and
`cold-only`. Controlled trials require a fresh cache for each task repetition,
one reusable server within the task, and no cross-task reuse. Use a different
run ID for route-native behavior.

Known capacities require at least one numeric limit. Opaque provider-managed
runtime/capacity is valid only when explicitly labeled opaque and supported by
a proof; it never becomes zero. `hit_status` is `observed`, `none-observed`, or
`unavailable`. Unavailable counters remain null and make speed unavailable.

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

Cache profile, reset boundary, and reuse-scope drift blocks comparability.
Runtime, cache engine, and capacity may differ across exact routes because they
are route identity. If the same exact route has different cache configuration
or downstream-attribution fingerprints, comparison blocks. Cached-input pricing
is never cache-hit proof.

## Router and mixed-route attribution

`provenance.route.routing_mode` is `direct`, `router`, or `mixed`. Direct routes
must not include a downstream block. Router and mixed routes require:

```json
{"downstream":{"complete":true,"coverage_proof":{"kind":"trace-index","reference":"artifact://..."},"observations":[{"provider":"local","model":"qwen","cache_configuration_fingerprint":"sha256:...","fallback_used":false,"identity_proof":{"kind":"trace","reference":"artifact://..."},"cache_proof":{"kind":"trace","reference":"artifact://..."},"fallback_proof":{"kind":"trace","reference":"artifact://..."}}]}}
```

The comparator fingerprints normalized downstream identity/cache/fallback
observations. Missing coverage, proof, cache fingerprint, or explicit no-fallback
state makes the route non-comparable; an outer router alias is never sufficient.

Cost fields become n/a when pricing provenance is unavailable; capability
comparison remains valid. Missing
failure-mode evidence is n/a; an explicit empty count map means no failures were
recorded.

The value objective requires all three lane floors:

    --min-score 0.70 --min-reliability 0.80 --min-worst-of-n 0.55

--require-pass-hat-k optionally requires overall_pass_hat_k equal to 1. With no
complete floor set, the value read is unavailable-floor. If neither route
passes, it is no-eligible-route; price never rescues an incapable route.
