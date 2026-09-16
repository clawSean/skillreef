# Research and Retrieval Routing

## Public discovery and known URLs

1. Use native `web_search` for discovery, current facts, and source finding.
2. Use native `web_fetch` for a known public page without JavaScript/login.
3. Prefer primary/authoritative sources and fetch them before consequential
   claims or action.
4. Use a domain API/skill first when its data is authoritative and structured.

Search snippets are leads, not final evidence. Browser automation is not a
better fetcher when readable public text is already available.

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
