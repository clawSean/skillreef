---
name: "model-manager"
description: "Audit or add cloud and local models, diagnose model-route failures, reconcile provider catalogs, and prove agent exposure."
---

# Model Manager

Manage cloud and local model lifecycles from discovery through verified activation; keep default promotion a separate, explicit decision.

## Procedure

1. Freeze the requested state: discovery-only, catalog reconciliation, selectable activation, agent exposure, qualification, or default promotion. Treat install, runtime upgrade, model download, live config write, plugin mutation, service start, and Gateway restart as separate approval boundaries. Complete when authorized mutations and prohibited defaults/fallback changes are explicit.

2. Capture the live baseline without secrets. Read the installed OpenClaw model docs and current CLI help, then run `openclaw models status --json`, `openclaw models list --all --json`, and `openclaw agents list --json`. Record the OpenClaw version, configured providers, aliases, allowlist, primary/fallback/utility models, auth or route issues, and each configured agent's inherited or explicit model policy. Complete when the before-state can detect collateral changes.

3. Discover current models from first-party provider catalogs and release notes. Use `openclaw models refresh --json` only when the installed CLI supports it and the live ownership boundary permits it; if it requires offline ownership, do not stop the Gateway merely to refresh. Use the running Gateway's supported catalog route or existing authenticated catalog and mark freshness limits. For providers whose configured catalog is authoritative or incomplete, compare the provider's official catalog with the installed OpenClaw plugin/docs and live config. Record exact model IDs, availability/preview status, entitlement, input modes, reasoning/tool support, context/output limits, and deprecation or replacement notes. Never infer capabilities from a family name.

4. Reconcile six states separately: **discoverable**, **cataloged**, **selectable**, **auth-usable**, **canary-proven**, and **promoted**. “All models available” means the full upstream catalog is discoverable and every intentionally supported frontier or role-specific route is selectable; it does not mean copying every OpenRouter or provider SKU into the allowlist. Complete when omissions are classified as stale catalog, missing configured entry, auth/entitlement gap, intentional exclusion, or unqualified route.

5. Follow the provider branch in [references/provider-and-local-routing.md](references/provider-and-local-routing.md). Use installed specialist skills for custom Claude routing, OpenAI account/runtime routing, and local MLX onboarding when available; otherwise follow the bundled provider reference and official runtime docs. Complete when one canonical owner controls each provider/model fact.

6. For an approved catalog or activation change, use supported validated `openclaw config` commands to change only the exact canonical provider catalog, `agents.defaults.models` picker entries, `agents.defaults.modelPolicy.allow`, and any agent-specific policy entries required for the route. Picker registration and execution permission are separate gates; do not assume one implies the other. Preserve unrelated models, array order, defaults, fallbacks, utility models, auth profiles, and account selection. Give aliases to stable roles or owner-requested names; retain an old explicit route when compatibility still matters. Re-read and semantically diff the protected arrays before validation.

7. Validate with `openclaw config validate`, `openclaw models status --json`, and provider-filtered `openclaw models list --provider <id> --json`. Require no new missing-provider or route issues and verify each alias resolves exactly once. When a write should hot-load, capture the Gateway PID and require the reload log to classify it as hot; stop if a restart is queued without approval.

8. Prefer a fresh Gateway-backed `openclaw agent --agent <id> --session-key agent:<id>:model-canary-<unique> --model <provider/model> --thinking low --timeout 180 -m 'Reply with exactly: MODEL_ROUTE_OK' --json` without `--deliver`. Confirm current help and override fallback behavior first. Avoid isolated `agent exec` for shared OAuth proof unless its auth-store visibility is established. Run a minimal exact-model canary with fallback disabled for every newly activated route or materially changed backend. Require a terminal result, expected provider/model winner, non-empty sentinel, and actual response model or billing metadata when the provider exposes it. Catalog and request metadata prove routing intent; only terminal provider evidence proves which model served tokens. Use a realistic cold-start budget for local models. If a bare provider smoke returns `200` but the agent turn fails with a generic `400` schema/tool wrapper, compare the **same** auth profile, transport, model, tools, parameters, and conversation payload; inspect the provider error code when available before assigning the fault to tools or the model.

9. Prove agent exposure separately. Re-read every configured agent after the change; verify inherited defaults and explicit per-agent pins without broadening private/local-only boundaries. Canary each materially different catalog policy or execution lane. Keep local-only agents fail-closed with no cloud fallback unless separately approved.

10. Report a compact provider matrix with newest/best candidate, exact route, six-state status, intended agents, evidence, exclusions, and blockers. Record durable architecture decisions in the owning project/status or knowledge procedure, not in this skill. Complete when another run can reproduce the result without treating discovery as activation or activation as promotion.

## Local and Hugging Face branch

1. Locate and read the installation's local-model fleet instructions, manifest, residency/cache policy, decisions, and onboarding procedure. Treat the host's measured physical memory as a shared ceiling for macOS, Gateway, model runtime, caches, and ComfyUI; use measured peak RSS, pressure, and swap rather than weight-file size.

2. Pin the exact Hugging Face repository revision, model files, hashes, license, chat template, tokenizer/processor, quantization, context claim, and intended role. Prefer role diversity over duplicate quants; do not download multiple large variants without a reproducible quality or compatibility reason.

3. Select the runtime from architecture evidence. Prefer `mlx-lm` for supported text-only architectures and `mlx-vlm` for supported multimodal or newer/custom architectures. Keep existing Ollama routes on their own lifecycle contract. Use another engine only from its official Apple Silicon support and cache/tool protocol; never transplant MLX flags by analogy.

4. Follow `local-mlx-model-onboarding` when installed, or the fleet's canonical onboarding procedure, for snapshot, service, cache, residency, direct-generation, Gateway-route, and promotion gates. Keep the shared residency lock, explicit reservation, loopback binding, offline pinned snapshot, idle eviction, and exclusive reservation for the largest route. Coordinate ComfyUI through the same memory-pressure admission boundary; ComfyUI assets are media-workflow models, not chat-provider entries.

5. Put compatibility fixes at the shared runtime/provider boundary so every authorized agent and caller inherits them. Preserve physical provider/model identity for lifecycle, cache namespace, health, session pinning, and logging even when the UI later groups local models.

## Hard stops

Stop on unverified model IDs, preview access mistaken for general availability, provider-side fallback, ambiguous winner metadata, missing license, unsupported tokenizer/tool parser, raw protocol leakage, unbounded local residency, memory pressure or swap, unexpected restart, or collateral default/fallback/auth changes. Preserve the candidate as discovered or staged and report the blocked gate.
