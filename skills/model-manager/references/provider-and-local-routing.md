# Provider and local routing

Read only the matching branch. Verify installed CLI help and first-party provider docs every run.

## OpenAI

- Use the built-in catalog and authenticated account-scoped discovery when available.
- Refresh through a supported live route; an offline-ownership refusal is not permission to stop or restart the Gateway.
- Keep API-key and Codex subscription/OAuth lanes distinct. Use an installed account-routing specialist when available; otherwise inspect runtime and auth-profile status without exposing credentials.
- Prove shared OAuth through a fresh Gateway-backed agent turn. Isolated exec may use a different auth store.
- Require terminal response-model metadata and no fallback, not just an alias or request model.

## Claude / Anthropic

- Detect whether built-in Anthropic or a custom subscription router owns the route; inspect that owner's manifest, docs, and account state before changes.
- Keep provider IDs, runtime IDs, and plugin IDs distinct. Do not assume their names match.
- Use a matching account-routing skill when installed; otherwise follow the detected provider's official configuration contract.
- For subscription-OAuth 400 errors, compare the installed release's advertised client version and beta headers with the exact model's minimum requirements. API-key success may exercise a different transport.
- If a minimal exact-route canary works but a normal turn fails, compare tools, parameters, history, transport, and auth profile before assigning the cause.

## OpenRouter

- Inspect the hosted catalog rather than copying every SKU into config.
- Preserve upstream vendor/model IDs and tier suffixes.
- Add only requested, frontier, or distinct-role routes. Prove account, region, routing policy, and entitlement with an exact-model canary.

## NVIDIA and Venice

- Compare official provider catalogs with plugin catalogs and configured model definitions.
- Add targeted entries with verified limits and capabilities; never infer them from the family name.
- Qualify native routes independently from mirrors on other providers.

## xAI, Google, and other cloud providers

- Prefer authenticated native provider integrations when supported.
- Treat preview, regional, beta, and account-gated models as discovered until the account succeeds.
- Add cross-provider role aliases only when requested.

## Local chat and coding models

- Discover the installation's canonical fleet manifest, onboarding procedure, service definitions, cache policy, and residency owner.
- Use a local onboarding skill when installed; otherwise require pinned weights/revision/hashes/license, supported runtime and tokenizer/tool parser, bounded residency, measured memory pressure, and direct plus Gateway canaries.
- Keep per-route ports, commands, cache namespaces, reservations, and idle lifecycle distinct even when the UI groups local models.
- Never download large variants or start services beyond the authorized scope.

## Agent exposure

- Generate the roster from live configuration. Separate inherited model maps from per-agent allowlists, pins, and fallbacks.
- Keep local-only agents fail-closed without cloud fallback.
- For project-scoped coding agents, qualify file containment and execution permissions separately from model availability.
- Describe staged agents as staged until live roster and route proof exist.

## Local media tools

- Treat ComfyUI and other media engines as separate workflows, not chat models.
- Coordinate storage, licenses, residency, and memory admission with the local inference fleet.
