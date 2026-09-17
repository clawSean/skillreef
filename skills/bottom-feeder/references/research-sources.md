# Research Sources

## Core Principle

Use the source categories that fit the question and triangulate when independent
source types materially improve confidence. Load `web-use` for generic search,
fetch, research-provider, browser, extraction, and fallback routing. Do not keep
a competing provider ladder here.

## Source Categories

### 1. Public discovery and current facts
Search engines, AI-assisted search, news aggregators, and known-URL fetches.
Describe the evidence need to `web-use`; it selects the concrete provider and
does not require a fixed number of queries. Add queries only when uncertainty,
source diversity, or contradiction risk warrants them.

Capture: title, URL, key claim, publication date.

Default module hint:
- Let `web-use` select the native search/fetch provider or specialist leapfrog.
- Use about 5 results by default, with locale matched to the topic.
- Routine runs may skip web lookup when local/internal authoritative sources
  already answer the question.

### 2. Page Fetching & Extraction
When search snippets are insufficient, fetch and read full pages. Use browser tools for JS-rendered content, fetch tools for static pages.

Routine mode: fetch only the pages needed to answer the question. Burn/fleet
may widen fetch depth when the evidence plan justifies it.

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

### 8. Deep synthesis / cited research
When the topic needs difficult cross-source synthesis, contradiction hunting,
or richer citation discovery, ask `web-use` to route to its cited-research
specialist (currently the standalone Perplexity skill when installed). Do not
reimplement that provider's API or preset policy here.

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

- **Routine:** Local knowledge first, then the lightest fitting web-use route.
- **Burn/fleet:** Broaden relevant source categories and depth according to the
  evidence plan; never invoke every provider by ritual.

## Anti-Patterns

- Treating “use multiple providers” or “use everything” as a ritual rather than
  selecting the smallest dependable evidence mix.
- Skipping internal tools for team-related topics.
- Treating this list as exhaustive — if you have a relevant tool, use it.
- Fetching pages you don't need in routine mode.
