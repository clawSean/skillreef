# Local Cache Admission

This file is ClawGauge's single detailed protocol for local cache correctness.
The workspace onboarding procedure owns lifecycle/state transitions and links
here; dated audits record history only.

Cache admission proves that the exact local route reuses the right model state
without collisions or unsafe memory behavior. It does **not** prove agent
capability, truthfulness, or suitability for a work lane. Those belong to
operator qualification.

## Claim ladder

1. `cache-configured`: durable launch policy enables a cache.
2. `direct-service-prefix-reuse`: the generic qualifier proves cold/warm/replay
   reuse on one already-running loopback API.
3. `cache-qualified`: every frozen architecture-aware admission case passes,
   its artifacts are content-bound, and a current OpenClaw route observation
   proves exact model/runtime identity plus `fallback=false`.
4. `operator-qualified`: separate ShellBench, truthfulness, and Personal Agent
   QA gates pass.
5. `promoted`: explicit routing decision and approved live change.

Never collapse these states.

## Direct-service screen

Run `qualify_prefix_cache.py` with exact runtime, MLX core version, immutable
model revision, and a fresh cache epoch. A pass grants only
`direct-service-prefix-reuse`.

Required observations:

- cold cached tokens equal zero;
- append-only warm reuse clears the declared token floor;
- exact replay returns a fresh response ID and reuses more input than warm;
- all responses report the requested model;
- listener PID/start time remain stable and peak RSS is captured;
- MLX-VLM additionally proves APC health, reset, positive exact hit/store
  deltas, and no disk activity/configuration.

This direct-service screen cannot prove the OpenClaw provider route, fallback
absence, auxiliary recurrent state, media identity, tenant isolation,
eviction safety, `cache-qualified`, or `operator-qualified`.

## Frozen admission plan

Build `clawgauge.local-cache-admission-plan.v2` with:

- exact runtime/runtime version and MLX version;
- exact OpenClaw provider, API response model, loaded model, and immutable model revision;
- installed OpenClaw version and immutable OpenClaw commit;
- SHA-256 fingerprints for architecture, template, parser, cache policy, and
  cache layout;
- exactly one structural feature: `standard-kv`, `hybrid-recurrent`, or
  `rotating-or-conv`;
- exactly one modality: `text-only` or `multimodal`;
- exactly one service scope: `isolated-service` or `shared-service`;
- exactly one batching mode: `serial-service` or `batched-service`.

Unknown or ambiguous architecture blocks execution. Do not default a route to
standard KV.

## Required cases

Every executable plan includes:

- `declaration-provenance`: requested/observed route, `fallback=false`, exact
  runtime/model/OpenClaw identity, fingerprints, and runtime epoch;
- `cold-warm-replay`: cold zero, warm reuse, replay growth, fresh ID, same
  PID/start/epoch, output parity, and RSS;
- `mutation-matrix`: system, tools/order, reasoning, template, revision,
  media, and tenant mutations invalidate the affected state;
- `memory-lifecycle`: peak RSS, pressure, swap, saturation/eviction, idle/exit,
  and route-handoff behavior.

Conditional cases:

- `stateful-branch-replay` for hybrid/recurrent/rotating/conv state: clean cold
  A, warm A, branch B, return A, and a fresh cold-A reference;
- `media-key-isolation` for multimodal routes: media A cold/warm, media B no
  collision, cold-B parity, and same-path changed-content invalidation;
- `tenant-and-eviction-isolation` for shared services: independent tenant salts,
  concurrent prefixes, no cross-tenant hit, bounded eviction, and parity after
  eviction;
- batch parity before concurrency >1: single output must equal output when
  co-batched with both shorter and longer peer rows. The frozen plan emits
  `batch-parity` whenever `batched-service` is declared.

Qwen3-Coder-Next is hybrid: MLX-LM uses recurrent/conv arrays plus full-attention
KV state. It requires branch replay even though its public name says Coder.

## Result and score contract

Execute every plan case and record
`clawgauge.local-cache-admission-results.v1`:

- exact plan fingerprint and plan artifact SHA-256;
- byte-equal plan provenance;
- every expected case exactly once, each `status=pass`;
- at least one safe relative, SHA-256-bound evidence artifact per case;
- a content-bound `clawgauge.local-model-architecture.v1` manifest;
- a content-bound `clawgauge.local-route-observation.v1` artifact with exact
  requested provider/model, observed provider/model, response model, loaded
  model, runtime provenance, positive PID, start time, runtime ID, cache epoch,
  and `fallback_used=false`.

Score with `validate_local_cache_admission.py`. Missing, extra, duplicated,
failed, stale, mismatched, unsafe, or tampered evidence blocks. Only the
content-bound `clawgauge.local-cache-admission-score.v1` may grant
`cache-qualified`. Bind that score under `provenance.cache.admission` in each
ClawGauge evidence envelope.

## Runtime floors and caveats

- New MLX-VLM admission requires `mlx-vlm >=0.6.15`; pair it with the exact MLX
  core version used in proof. `0.6.15` includes batching/padding corrections and
  MLX `0.32.1` compatibility.
- `mlx-lm 0.31.3 --prompt-cache-bytes` is a trim target, not a hard ceiling.
  Nearest-prefix reuse may transiently copy state. Entry count plus measured
  RSS, memory pressure, and swap are the real safety gates.
- MLX-VLM exact snapshots are count-bounded, not byte-bounded; APC stats do not
  expose every byte of exact-snapshot residency.
- Hugging Face `past_key_values` can be retained between in-process
  `generate()` calls, but is not automatic HTTP prefix caching.
- Thinking-history policy is exact-model-specific. Pin the model card,
  template, and parser; do not apply one Qwen-family rule to every model.
- MLX-VLM tenant headers include `X-APC-Tenant` and `X-Tenant-Id`, with
  `APC_DEFAULT_TENANT` as a service default. A static shared header is not
  session isolation. Prove trusted per-session propagation or isolate services
  by trust domain.

## Official source pins

- MLX-VLM 0.6.15: <https://github.com/Blaizzy/mlx-vlm/releases/tag/v0.6.15>
- MLX 0.32.1: <https://github.com/ml-explore/mlx/releases/tag/v0.32.1>
- MLX-LM 0.31.3: <https://github.com/ml-explore/mlx-lm/releases/tag/v0.31.3>
- Hugging Face cache guide: <https://huggingface.co/docs/transformers/main/en/kv_cache>
- Qwen3.8-27B model card: <https://huggingface.co/Qwen/Qwen3.8-27B>
- Qwen3-Coder-Next model card: <https://huggingface.co/Qwen/Qwen3-Coder-Next>
- llama.cpp server cache: <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>
- vLLM prefix caching: <https://docs.vllm.ai/en/stable/design/prefix_caching/>
- vLLM-Metal models: <https://github.com/vllm-project/vllm-metal/blob/main/docs/supported_models.md>
- SGLang Apple backend: <https://docs.sglang.ai/platforms/apple_metal.html>
