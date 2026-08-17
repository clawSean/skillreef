# Local Cache Admission

Use this after the generic cold/warm/replay qualifier and before any
`cache-qualified` claim. Configuration, service residency, faster warm time,
and positive cached-token telemetry are necessary but not sufficient.

## Evidence contract

Record exact provider/model, immutable model revision, runtime and version,
OpenClaw commit, chat-template/tool/reasoning configuration, cache layout,
cache-policy fingerprint, listener PID/start/cache epoch, fallback=false, and
the artifact hash for every cell.

## Base gates

Every local route must prove:

1. fresh/reset cold, append-only warm, identical replay, and anti-response-memo
   evidence through `qualify_prefix_cache.py`;
2. exact cold-versus-warm output parity on deterministic fixtures;
3. semantic mutations invalidate the affected prefix;
4. current-OpenClaw two- or three-tool continuation with preserved reasoning,
   exact route identity, and no raw tool-text leakage;
5. frozen truthfulness and realistic lane screens at `n >= 3`;
6. cold load, cold/warm prefill, decode, tool, and total task timing;
7. peak RSS, host pressure, swap, saturation/eviction, and target context;
8. warm-before-idle, cold-after-exit, external reuse, and route handoff.

## Conditional gates

### Hybrid recurrent/GDN cache

Use branch replay: clean cold A, reset, warm A, branch B, return to A, then a
fresh cold-A reference. Compare state-sensitive outputs. Speed cannot prove
that auxiliary arrays were restored.

### Rotating, sliding, or convolutional cache

Exercise beyond the rotation/window boundary and compare restored warm output
with a cold reference. Ordinary KV success does not cover other cache children.

### Multimodal cache

Use identical text with media A cold, media A warm, then media B. A must reuse;
B must not collide and must equal a cold-B reference. Bind processed-media,
processor, and model hashes.

### Shared service

Use separate tenant salts and concurrent prefixes. Prove no cross-tenant hit,
correct longest-prefix selection, bounded eviction, and post-eviction parity.

## Runtime caveats

- `mlx-vlm 0.6.14` is the current minimum cache-fix release for new
  qualification. Older saved proofs remain historical.
- `mlx-lm 0.31.3` does not enforce `--prompt-cache-bytes` as a universal
  hard cap. Nearest-cache reuse can transiently copy state.
- MLX-VLM exact snapshots are count-bounded, not byte-bounded; APC stats omit
  some exact-snapshot memory.
- KV quantization is a separate memory/quality trade.
- Hugging Face `past_key_values`, model-file caches, and response memos are not
  cross-request prefix-cache proof.

## Official references

- MLX-VLM 0.6.14: <https://github.com/Blaizzy/mlx-vlm/releases/tag/v0.6.14>
- MLX-LM: <https://github.com/ml-explore/mlx-lm>
- MLX KV guidance: <https://github.com/ml-explore/mlx/blob/main/docs/src/usage/kv_cache.rst>
- Hugging Face KV cache: <https://huggingface.co/docs/transformers/main/en/kv_cache>
- llama.cpp server: <https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md>
- vLLM APC: <https://docs.vllm.ai/en/stable/design/prefix_caching/>
- SGLang cache: <https://docs.sglang.ai/advanced_features/hicache_best_practices.html>
- Ollama lifecycle: <https://docs.ollama.com/faq>
