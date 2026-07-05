# Provider Expansion Plan

Auth Molt starts Codex-only. Expand to other providers only when the conditions below are met.

## Current status

| Provider | Status | Notes |
|---|---|---|
| `openai-codex` | **Supported — proven** | Force-expiry trick verified on claw3 (2026-05-01). Script allowlist enforces this provider. |
| `claude-cli` / Anthropic | **Observed — unproven** | OAuth profile seen in auth store (`anthropic:claude-cli`) with provider `claude-cli`. OpenClaw can store access/refresh/expiry for it, but the refresh path has not been safely tested. claw4-style token reuse failure is possible. |
| All others | **Do not attempt** | No verified refresh path. `--all` across providers is blocked by current allowlist. |

## Expansion prerequisites

Before adding a new provider to the allowlist (`CODEX_RE` → provider-specific regex):

1. **Confirm `type: oauth`** — provider must be OAuth, not apikey or static.
2. **Confirm OpenClaw has an OAuth manager/plugin for it** — inspect `/usr/local/lib/node_modules/openclaw/dist/` for a matching oauth/provider module.
3. **Confirm a refresh path exists** — the manager must support token refresh (not just initial auth). Check for `refresh_token` usage in the provider module.
4. **Test with a single profile in dry-run first**, then force-expired on a non-critical profile.
5. **Update provider-specific allowlists** only for the proven profile pattern. Do not generalize to every profile with `type: oauth` until refresh has been tested provider-by-provider.

## Claude CLI / Anthropic — what we know

- Auth profile `anthropic:claude-cli` exists locally with `type=oauth`, provider `claude-cli`, and access/refresh/expiry fields.
- The 401 may indicate a stale or revoked OAuth credential. Force-expiry trick may not help if the refresh token is also dead.
- **Recommended path**: verify the profile is still needed before attempting refresh. If needed, inspect the OpenClaw/Claude CLI provider refresh path, then try standard `resolveApiKeyForProfile` against this profile without force-expiry first. Only add to allowlist after a successful non-critical test.

## Direct POST fallback

If OpenClaw's `resolveApiKeyForProfile` cannot handle a provider, the last resort is a direct OAuth token refresh POST:

```
POST <provider-token-endpoint>
grant_type=refresh_token
refresh_token=<stored-refresh-token>
client_id=<provider-client-id>
```

Only use this if:
- The provider's OAuth spec is known and the token endpoint is documented.
- The client_id is available (not secret-only flow).
- No OpenClaw helper covers the refresh.

This approach bypasses OpenClaw's file-lock and store-update logic — you must write the result back to the auth store manually with proper chmod and backup. Use with extreme caution.
