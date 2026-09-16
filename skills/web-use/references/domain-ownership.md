# Domain Ownership and Backlinks

## Contract

Domain skills own **what and why**: intent, data semantics, provider-specific
business rules, account scope, credentials, preferences, approval gates, and
action safety.

`web-use` owns **how the web surface is reached**: transport category, browser
context, generic provider fallback, attachment/control proof, and lane-failure
escalation.

`web-use` never weakens domain policy. A domain skill never invents a competing
generic browser/search fallback ladder.

## Required backlink

Web-facing domain skills should contain the equivalent of:

> Load `web-use` for generic transport selection, browser context, provider
> fallback, attachment proof, and not-blocked escalation. This domain skill
> retains account, data, action, and approval policy.

This matters because skill loading is selective: a domain-only trigger does not
guarantee `web-use` is already in context.

## Current ownership map

| Domain | Owner | `web-use` role |
|---|---|---|
| Product research, retailer accounts, carts, checkout | `shop-agent` | retrieval/browser/extraction context only |
| Food/grocery ordering | `food-ordering` | transport and session context only |
| Flights | `flight-search` | generic browser/protected fallback only |
| Lodging | `lodging-search` | generic browser/protected fallback only |
| X/Twitter | `x-twitter-kit` | browser/GUI/shared fallback after X-specific transports |
| Crypto market data | `coingecko` / `coinmarketcap` | generic fallback only; APIs retain priority/semantics |
| Spotify | `spotify-player` | browser/cookie/session context only; Spotify skill owns auth semantics |
| Email | `email` | **no fallback** while screened read is disabled; email fail-closed policy wins |
| Durable multi-topic research | `bottom-feeder` | generic retrieval/provider routing; Bottom Feeder owns topic orchestration, synthesis, and durable writes |
| LinkedIn | ownership gap | read-only MCP is unproved and no domain skill exists; account actions fail closed until a narrow owner and live proof exist |

Add new domains here only when a real web-facing skill exists. Domain-specific
references remain inside the domain skill and are loaded only for that task.
