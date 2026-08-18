# ClawGauge Evidence Envelope v3

ClawGauge compares `clawgauge.evidence.v3` envelopes, not naked ShellBench JSON.
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
that key. Version 3 requires:

- `claim_scope`: `route-operational`, `model-isolation`, or `cache-ablation`;

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

Ordinary proofs are objects with non-empty kind and reference strings. Cache
speed claims additionally require a relative, content-hashed
`clawgauge-cache-events` artifact. A boolean or handwritten cache summary is
not speed evidence. References never contain secrets or absolute local paths.

## Truthfulness provenance

`provenance.truthfulness` is optional for a capability-only comparison but
required for any trust or decision-grade claim. It binds a content-hashed
`clawgauge.truthfulness-score.v1` artifact:

```json
{
  "passed": true,
  "suite_sha256": "sha256:...",
  "route_sha256": "sha256:...",
  "repetitions": 3,
  "case_count": 8,
  "expected_cells": 24,
  "score_proof": {
    "kind": "clawgauge-truthfulness-score",
    "reference": "truthfulness-score.json",
    "sha256": "sha256:..."
  }
}
```

The score must pass with complete per-cell execution attribution and its exact
requested/observed provider, model, adapter, reasoning, fast, and fallback
state must match the envelope route. The compared routes must use the same
suite, repetitions, case count, and cell count. Missing evidence does not erase
valid capability measurements, but it makes trust/decision-grade status false.
An invalid supplied truthfulness block fails envelope validation.

## Personal Agent QA provenance

`provenance.qa` is optional for capability-only comparison and required for
decision-grade status. It binds the content-hashed JSON emitted by
`score_qa_suite.py`:

```json
{
  "passed": true,
  "profile": "personal-agent",
  "scenario_count": 10,
  "model": "exact/provider-model",
  "fast_mode_effective": false,
  "score_proof": {
    "kind": "clawgauge-qa-scorecard",
    "reference": "qa-gate.json",
    "sha256": "sha256:..."
  }
}
```

The scorecard must be comparable, contain exactly one record for the observed
model, use live-provider evidence, keep fallback disabled, match effective fast
state, contain the exact ten Personal Agent scenarios, pass every scenario on
every retained attempt, and contain no blocked/stalled/skipped/failed retry.
Missing QA leaves capability evidence usable but decision-grade false. An
invalid supplied QA attestation blocks envelope validation.

## Cache provenance

`provenance.cache` has six required blocks: `runtime`, `layers`,
`configuration`, `protocol`, `lifecycle`, and `observed`.

```json
{
  "runtime": {
    "visibility": "known",
    "kind": "prefix-kv",
    "name": "mlx-vlm",
    "version": "0.6.15",
    "engine": "automatic-prefix-cache"
  },
  "layers": [
    {
      "kind": "prefix-kv",
      "enabled": true,
      "name": "mlx-vlm",
      "version": "0.6.15",
      "engine": "automatic-prefix-cache"
    },
    {
      "kind": "full-response-memoization",
      "enabled": false,
      "name": "response-memo",
      "version": "1.0.0",
      "engine": "disabled"
    }
  ],
  "configuration": {
    "enabled": true,
    "persistence": "process-memory",
    "effective_knobs": {
      "eviction_policy": "lru",
      "max_prefix_tokens": 32768,
      "minimum_prefix_tokens": 1
    },
    "capacity": {
      "visibility": "known",
      "limits": {"tokens": 32768, "entries": 2048}
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
    "gross_input_tokens": 156000,
    "response_memo_hit_count": 0,
    "hit_metric": "cached_input_tokens",
    "hit_rate": 1.0,
    "cold_latency_ms": {"p50": 3400, "p95": 6100},
    "warm_latency_ms": {"p50": 700, "p95": 1200},
    "startup_latency_ms": {"p50": 900, "p95": 1100},
    "readiness_latency_ms": {"p50": 100, "p95": 150},
    "ttft_latency_ms": {"p50": 500, "p95": 900},
    "prefill_latency_ms": {"p50": 400, "p95": 800},
    "decode_latency_ms": {"p50": 200, "p95": 400},
    "peak_process_rss_bytes": 17179869184,
    "peak_accelerator_bytes": 12884901888,
    "peak_cache_resident_bytes": 2147483648,
    "peak_cache_resident_tokens": 32768,
    "cache_evictions": 0,
    "hit_proof": {"kind": "request-telemetry", "reference": "artifact://..."},
    "trace_proof": {
      "kind": "clawgauge-cache-events",
      "reference": "route-a-cache-events.json",
      "sha256": "sha256:..."
    }
  }
}
```

For an enabled known MLX runtime, decision-grade status additionally requires
`provenance.cache.admission` bound to a passing architecture-aware score:

```json
{
  "passed": true,
  "plan_fingerprint": "sha256:...",
  "case_count": 5,
  "score_proof": {
    "kind": "clawgauge-local-cache-admission-score",
    "reference": "local-cache-admission-score.json",
    "sha256": "sha256:..."
  }
}
```

The comparator verifies the score schema, blockers, exact runtime/version,
observed provider/model, OpenClaw commit, cache-policy fingerprint,
architecture features, and architecture/template/parser/cache-layout
fingerprints. The bound score itself includes the exact response/loaded model,
installed OpenClaw build, immutable revisions, and route observation. Missing
admission preserves directional capability evidence but makes decision-grade
false. A supplied invalid or mismatched admission blocks validation. See
`local-cache-admission.md`; direct-service cold/warm/replay proof alone is not
admission.

Every layer has a unique supported `kind`, a boolean `enabled`, and non-empty
`name`, `version`, and `engine`. Exactly one
`full-response-memoization` layer is mandatory even when disabled. Exactly one
layer must match `runtime.kind`, and that layer's enabled state must equal
`configuration.enabled`.

`configuration.effective_knobs` is a non-empty JSON object containing the
effective runtime values, not merely requested flags. Keys are non-empty
strings; nested objects and arrays are allowed; numeric values must be finite.
The configuration fingerprint is:

```text
sha256(UTF8(canonical_json({
  "runtime": {"visibility", "kind", "name", "version", "engine"},
  "enabled": configuration.enabled,
  "persistence": configuration.persistence,
  "effective_knobs": configuration.effective_knobs,
  "capacity": {"visibility", "limits"},
  "layers": layers_sorted_by_kind[{"kind", "enabled", "name", "version", "engine"}]
})))
```

Canonical JSON uses sorted keys, compact separators, and UTF-8. Proofs are
excluded. Both `configuration.fingerprint` and
`observed.configuration_fingerprint` must equal this exact digest; changing an
effective knob or layer identity without recomputing it blocks the envelope.

Cache kind is mandatory: `prefix-kv`, `residency-only`,
`full-response-memoization`, `embedding-result`, or
`opaque-provider-managed`. Opaque runtime visibility requires the opaque kind,
a null runtime version, and proof. Known runtimes require a version.
Residency-only may not claim request hits or reused input tokens;
embedding-result may not claim reused model-input tokens. Every envelope must
report a non-negative `response_memo_hit_count`, and it must be zero. When the
response-memo layer is enabled, a valid cache-events v2 trace with
`response_memo_hit: false` on every request is also mandatory. Distinct outputs
alone do not disprove response memoization.

Allowed profiles are `route-native`, `controlled-cold-then-warm`, and
`cold-only`. Controlled trials require a fresh cache for each task repetition,
one reusable server within the task, and no cross-task reuse. Use a different
run ID for route-native behavior.

Known capacities require at least one numeric limit. Opaque provider-managed
runtime/capacity is valid only when explicitly labeled opaque and supported by
a proof; it never becomes zero. Disabled cache uses capacity visibility
`not-applicable` with empty limits. `hit_status` is `observed`,
`none-observed`, or `unavailable`. The only accepted hit metrics are `cache_n`,
`cached_input_tokens`, `prompt_tokens_cached`, and
`prompt_tokens_details.cached_tokens`. Unavailable counters and metric remain
null and make speed unavailable. Otherwise, hit count, reused tokens, and the
metric are required; `hit_proof` is required in every state. Cold/warm request
counts must sum to the positive total; latency is null only when its
corresponding count is zero. `cold-only` requires reset=true,
within-task-reuse=false, and cross-task-reuse=false.

## Cache-events v2 speed proof

Speed and cache-ablation claims require a relative, content-hashed
`clawgauge.cache-events.v2` artifact. Build it from normalized events and the
three independent source artifacts:

```bash
python3 scripts/build_cache_trace.py normalized-events.json \
  --out <artifact-root>/route-a-cache-events.json \
  --proof-out <artifact-root>/route-a-cache-proof.json \
  --hit-metric cached_input_tokens \
  --runtime-log <artifact-root>/runtime.jsonl \
  --openclaw-trace <artifact-root>/openclaw-trace.jsonl \
  --parser-artifact <artifact-root>/cache-parser.py \
  --parser-name <parser-name> --parser-version <parser-version>
```

The runtime log, OpenClaw trace, and parser must reside under the output
artifact root. The trace's `source.runtime_log` and `source.openclaw_trace`
contain relative `reference` plus exact `sha256`; `source.parser` additionally
contains non-empty `name` and `version`. The outer `trace_proof` hashes the
entire cache-events artifact. Every hash is exactly `sha256:` followed by 64
lowercase hexadecimal characters.

The artifact has top-level `schema_version`, one allowlisted `hit_metric`, the
source block, and a non-empty `events` array. Every request event requires:

- identity and phase: `task_id`, positive `repetition`, zero-based
  `turn_index`, unique `request_id`, and `phase` (`cold` or `warm`);
- exact route/lifecycle: `provider`, `model`, `fallback_used: false`, positive
  `backend_pid`, `backend_started_at`, `runtime_id`, `cache_epoch`, and the
  exact `cache_configuration_fingerprint`;
- content and lineage: exact-SHA `prompt_fingerprint`, `prefix_fingerprint`,
  `next_prefix_fingerprint`, and unique `openclaw_event_fingerprint`; cold
  events have no parent and set `append_only: false`; warm events require
  `parent_request_id`, exact-SHA `parent_prompt_fingerprint`, and
  `append_only: true`;
- token and memo telemetry: non-negative `gross_input_tokens`,
  `cached_input_tokens`, `uncached_input_tokens`, and `written_input_tokens`,
  plus `response_memo_hit: false`; gross must equal cached plus uncached,
  written cannot exceed gross, and cold cached input must be zero;
- tool binding: `tool_call_ids` and exact-SHA
  `tool_result_fingerprints` arrays of equal length; arrays may be empty, but
  every present ID is non-empty and unique across the trace;
- durations: non-negative `startup_ms`, `readiness_ms`, `ttft_ms`,
  `prefill_ms`, `decode_ms`, `request_wall_ms`, `tool_wall_ms`, and
  `task_wall_ms`;
- timestamps: monotonic `task_started_at_ms`, `request_started_at_ms`,
  `first_token_at_ms`, `request_completed_at_ms`, `tool_completed_at_ms`, and
  `task_completed_at_ms`; TTFT, decode, request, tool, and task durations must
  equal their timestamp deltas, and prefill cannot exceed TTFT;
- memory: positive `process_rss_bytes` plus non-negative
  `accelerator_active_bytes`, `accelerator_peak_bytes`,
  `cache_resident_bytes`, `cache_resident_tokens`, and `cache_evictions`;
  active accelerator memory cannot exceed peak.

Coverage must equal every BenchmarkResult task/repetition pair. Within each
pair, turns are contiguous, exactly one cold turn leads, every subsequent warm
turn links to the immediately preceding request and prompt, its prefix equals
the preceding `next_prefix_fingerprint`, and the preceding event contains a
tool result. The backend process/runtime/cache epoch and task span stay stable
inside the pair; model/tool spans cannot overlap; prompt fingerprints do not
repeat. Controlled prefix-KV trials require a positive cached-token count on
every warm turn. Reset boundaries require distinct cache epochs.

The comparator derives and cross-checks request/cold/warm/hit counts, reused
and gross input tokens, response-memo hits, hit status/metric/rate,
cold/warm/startup/readiness/TTFT/prefill/decode p50/p95, peak process and
accelerator memory, peak cache bytes/tokens, and evictions. All corresponding
`observed` aggregates must match. Derived end-to-end task-wall p50/p95 must
equal the native BenchmarkResult median/p95 latency. Handwritten summaries,
cached-input billing, or the lightweight prefix qualifier are not substitutes
for this trace.

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
are route identity. Route-operational comparisons may use the actual adapters
of each exact route but make route-level claims only. Model-isolation requires
matching runtime/prompt/tool/adapter controls. Cache-ablation additionally
requires the same exact route and valid raw cache events. If the same exact
route has different cache configuration outside cache-ablation,
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
