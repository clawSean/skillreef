# Research Sources

## Core Principle

Use ALL tools available in your current environment. Do not default to a single search provider. Every topic deserves multiple source types — triangulate.

## Source Categories

### 1. Web Search (any provider)
Search engines, AI-assisted search, news aggregators. Use whatever search tools are available (web_search, perplexity, etc.). Run 2-3 differently-worded queries per topic to catch different angles.

Capture: title, URL, key claim, publication date.

Default module hint:
- `web_search`/Brave-style search is the routine baseline.
- Use about 5 results by default, with `country: US` / English unless the topic calls for another locale.
- Use it in every routine run unless the user disables web lookup.

### 2. Page Fetching & Extraction
When search snippets are insufficient, fetch and read full pages. Use browser tools for JS-rendered content, fetch tools for static pages.

Routine mode: 2-3 pages max. Burn/fleet: fetch aggressively.

Default module hint:
- Browser extraction is optional, not the default.
- Keep it selective in routine runs, especially for JS-heavy or login-adjacent sites.
- Prefer stable docs and primary sources over noisy marketing pages.

### 3. Local Knowledge Base
Search `knowledge/`, `memory/`, and any indexed local content BEFORE hitting external sources. Existing coverage shapes what you need to find externally. Use knowledge-search skill or direct file search.

### 4. Internal Tools
Project management (Asana, Linear, Jira, GitHub Issues), team communication (Slack, Discord, Telegram), support platforms (Intercom, Zendesk), and any workspace-connected tools.

Highest-value source for operational and team-related topics. Internal data > web search for anything involving real people, real projects, or real decisions.

### 5. Code Repositories
Clone and read repos when the topic involves a specific project, library, or codebase. Shallow clone is fine. Read READMEs, changelogs, recent commits, open issues, architecture.

Use: `git clone --depth 1`, file reading, `gh` CLI for issues/PRs/releases.

### 6. Structured Data APIs
Crypto data (CoinGecko, CoinMarketCap), analytics, monitoring, or any domain-specific API available via MCP tools or skills.

Capture: quantitative data points with timestamps.

Default module hints:
- CoinGecko: use for price, 24h change, market cap/rank, volume, and trend direction when a topic touches tokens or markets.
- CoinMarketCap: use as a complement for token metadata, platform/contract mapping, and category tags. Do not treat it as mandatory for every crypto topic.

### 7. Social & Sentiment
Twitter/X, Reddit, Discord, community forums. Use for narrative pulse, not sole truth source. Always pair with at least one non-social source.

Default module hint:
- Use Twitter/X for narrative threads, notable accounts, and date/time context.
- Do not treat tweets as the sole truth source.
- Pair social signal with at least one primary, structured, or non-social source.

### 8. Deep Synthesis Providers
Use Perplexity or similar cited-synthesis tools only when the topic needs deeper cross-source synthesis, contradiction hunting, or richer citation discovery.

Capture: key claims, cited URLs, unresolved contradictions.

Routine guardrail: avoid paid/deep synthesis for low-cost smoke tests unless the user asks for depth.

### 9. Any Other Available Tool
MCP tools, skills, CLI utilities — if it's available and relevant, use it. The source list is not closed.

## Strategy by Topic Type

| Topic Type | Start With | Then Add |
|---|---|---|
| Operational/team | Internal tools, local knowledge | Web search for best practices |
| Technical/code | Code repos, docs | Web, social for community sentiment |
| Market/competitive | Web search, structured APIs | Social, internal strategy docs |
| Strategic/synthesis | Local knowledge, internal tools | Web to validate assumptions |

## Cost Awareness

- **Routine:** Local knowledge first, 1-2 search queries, selective page fetches.
- **Burn/fleet:** Everything. Multiple queries, aggressive fetching, all relevant APIs, full internal tool mining.

## Anti-Patterns

- Using only one search provider when multiple are available.
- Skipping internal tools for team-related topics.
- Treating this list as exhaustive — if you have a relevant tool, use it.
- Fetching pages you don't need in routine mode.
