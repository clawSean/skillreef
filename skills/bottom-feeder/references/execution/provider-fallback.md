# provider-fallback

Use fallback chains to keep Bottom Feeder productive when a provider is rate-limited or unavailable.

## Why

Long runs often fail from provider cooldowns (429), auth incidents, or transient outages. A single locked provider can burn an entire run window with zero output.

## Config

```yaml
provider_fallback:
  - anthropic
  - openai
fallback_after_consecutive_failures: 2
fallback_cooldown_minutes: 10
```

- Start on the first provider.
- Rotate to the next provider after N consecutive **qualified** failures.
- Also rotate if cooldown persists beyond the configured window.
- Stop gracefully if all providers are exhausted.

## Qualified failures

Rotate on:
- rate_limit / cooldown (429)
- auth failures (401/403)
- repeated transport/5xx failures
- quota exhausted

Do **not** rotate on:
- context overflow (fix model/prompt)
- tool misuse/errors unrelated to provider
- user stop

## Logging requirement

Every rotation should be appended to the run log:

```markdown
### Provider rotation
- Time: 2026-04-04T15:12:00Z
- From: anthropic
- To: openai
- Reason: 3 consecutive 429 errors
```

## Strict lock mode

If compliance requires a single provider, set `provider_lock` and omit fallback:

```yaml
provider_lock: anthropic
provider_fallback: []
```

In strict lock mode, stop-and-ask on failure.
