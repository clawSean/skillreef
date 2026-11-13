# Web Extraction Backends

Use these for public protected pages, repeated structured collection, or bulk
extraction. They are not the default research path and are not the normal home
for authenticated sessions.

## Placement in the ladder

1. Native `web_search` for discovery; `web_fetch` for known public URLs.
2. `perplexity-search` for source-backed synthesis or broad/multi-hop research.
3. Managed browser for ordinary JavaScript/rendering/interaction and logins.
4. Browserless for stateless protected public extraction.
5. TinyFish for deeper hosted multi-step public-browser control.
6. Installed domain API or scraper when its structured data/task fit wins.
7. Local visible browser or GUI/computer use only when that context is actually
   required; ask for a shared personal tab only when explicitly selected or
   after relevant self-sufficient lanes cannot supply the required context.

Do not deliberately walk every rung. Start at the lightest dependable lane that
fits the task.

## Bright Data: bounded structured public records

Use Bright Data's MCP selectively for fresh, structured public records when a
maintained site scraper materially improves on native fetch, first-party APIs,
or a one-off browser read—for example, dated competitor app reviews or repeated
marketplace product rows. Its SERP and `scrape_as_markdown` are fallback
transports, not default discovery or cited-synthesis routes. Do not use it as
the source of truth for an owned app's private metrics, ASO rank history, or
social-account actions. X-specific routing remains with `x-twitter-kit`.

Before a billed scraper run, inspect the exact scraper method and sample input;
bound source URLs, dates, and input count. `limit_per_input` is not a hard spend
cap: a prior Apple job requested 25 and delivered 211 records. Start with a tiny
pilot, inspect actual returned records and account metering, then expand only
when the task warrants it. MCP uses the same account-level credits as direct
API calls; full tool exposure does not make every tool free or appropriate.

Credentials and credits are account-specific. Verify the current agent's MCP
connection live before treating this as an available lane; do not export
authenticated browser state to Bright Data's hosted browser.

## Configured providers

### Browserless

Use for Cloudflare/anti-bot friction, hard public pages, and structured
extraction without a human-visible browser.

- Prefer stateless `/unblock` or `/stealth/bql`.
- Choose premium proxy or public anti-bot/Cloudflare solve settings only when a
  lawful public extraction blocker requires them. Never apply automated solving
  to login, account-security, transactional, or user-present challenges.
- Use `/session` only for demonstrated public same-site persistence; returned
  connection URLs are bearer credentials.
- The public Free plan currently advertises 1,000 units/month; units vary with
  duration, proxy, and CAPTCHA use. Verify pricing before optimizing around it.
- The bundled helper uses a stdlib-only HTTP path. The local registry owns
  whether a bounded public smoke is current enough for automatic use.

### TinyFish

Use when a hosted stealth browser needs deeper multi-step control. Prefer its
browser/session primitive for extraction; do not assume the higher-level Agent
API is automatically better.

TinyFish currently advertises free Search/Fetch plus metered Browser/Agent
usage and introductory wallet credit. Verify current pricing and balance before
paid use.

The bundled helper's HTTP path is stdlib-only; its CDP path requires a declared
WebSocket runtime. Do not use it automatically until the local registry records
dependency and bounded public-smoke proof.

## Candidate providers, not live capabilities

- Firecrawl currently advertises a monthly free credit allowance and is useful
  for crawl/map/scrape workloads, but it is not installed here.
- Apify currently advertises monthly free platform credit and is useful when a
  maintained Actor matches the site, but it is not installed here.

Do not route to either until its plugin/tool, credential, and smoke proof exist.
Install/activation remains approval-gated.

## Authentication boundary

Do not export or maintain authenticated cookies, localStorage, sessionStorage,
or signed-in state in Browserless, TinyFish, or another hosted provider by
default. The managed local profile is the dependable authenticated lane.

An exception requires explicit user authorization plus an owning domain policy
that accepts the privacy, cost, and persistence tradeoff. Never place secrets in
prompts, scripts, logs, committed examples, or chat.

## Failure discipline

- Distinguish data failure from browser-context failure.
- Switch providers when the task fit changes; do not loop on identical calls.
- A paid provider is acceptable when it materially improves accuracy or avoids
  wasted work, but log/verify the choice where the domain skill requires it.
- Keep login/account/transaction challenges out of hosted extraction. Route
  CAPTCHAs, 2FA, passkeys, and payment approval through the stable managed
  browser profile or an available local GUI lane.

## Helpers

- `../scripts/browserless_extract.py`
- `../scripts/browserless_session.py`
- `../scripts/tinyfish_browser_extract.py`

## Official pricing references

- Browserless: https://www.browserless.io/pricing
- TinyFish: https://www.tinyfish.ai/pricing
- Firecrawl: https://www.firecrawl.dev/pricing
- Apify: https://apify.com/pricing
