# Research and Retrieval Routing

## Public discovery and known URLs

1. Use native `web_search` for discovery, current facts, and source finding.
2. Use native `web_fetch` for a known public page without JavaScript/login.
3. Prefer primary/authoritative sources and fetch them before consequential
   claims or action.
4. Use a domain API/skill first when its data is authoritative and structured.

Search snippets are leads, not final evidence. Browser automation is not a
better fetcher when readable public text is already available.

## Exa: semantic discovery and enrichment

Use the existing Exa MCP when semantic search, finding related companies/people,
or building a deduplicated source set fits better than keyword search. Its
`web_search_exa` finds candidate sources and `web_fetch_exa` reads known URLs;
use `agent_run` for a genuinely multi-step collection/enrichment task. Do not
send a routine known-page read or simple fact lookup through Exa just because
it is connected. Verify the live MCP catalog and account access before relying
on it; one agent's connection says nothing about another agent's access.

Exa produces leads and extracted text, not authoritative app-review history,
rank tracking, or a substitute for checking consequential primary sources.

## Cited research

Route early to the standalone `perplexity-search` skill when the work requires:

- multi-source synthesis or comparison;
- difficult multi-hop reasoning;
- broad/source-heavy research;
- exhaustive or institutional-grade coverage;
- large evidence-backed collections with per-item research.

Use the narrowest sufficient Perplexity preset. The primary agent owns final
interpretation and checks material primary sources. Do not duplicate a simple
fact/known-page read with Perplexity merely because the provider is available.

Perplexity's quick-fact `fast` lane is intentionally not routine here because
native search/fetch already owns that category. Raw Perplexity Search,
embeddings, Router, finance search, and people search are not routine web-use
routes unless separately evaluated and admitted.

## Scraping placement

Scrapers belong after retrieval/research categorization. Use them for protected
public pages, bulk crawl/map, or repeated structured extraction—not ordinary
exploration. See `extraction-backends.md`.
