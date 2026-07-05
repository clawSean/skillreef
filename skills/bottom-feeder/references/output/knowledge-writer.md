# knowledge-writer

Write one file per topic immediately after synthesis.

Primary destination:
- `knowledge/topics/<topic-slug>.md`

Deep-dive destination:
- `knowledge/research/<YYYY-MM-DD>-<topic-slug>.md`

## YAML header

Include at the top of every knowledge file:

```yaml
---
title: <Topic Name>
crawled: <ISO timestamp>
mode: routine | burn | fleet
sources_used: [brave, perplexity, ...]
confidence: low | medium | high
tags: []            # optional — free-form labels for search/filtering
supersedes: ""      # optional — slug of a prior file this replaces
---
```

## Body sections

1. **Summary** -- 2-3 sentence overview (minimum 2; aim for 3 on broad topics).
2. **Current State** -- what is happening right now.
3. **Why It Matters** -- for our ecosystem/team/work. Be specific.
4. **Key Entities / Projects** -- named people, companies, repos, products.
5. **Open Questions** -- what we still do not know.
6. **Sources** -- each with access date. Mark paywalled or login-required sources.

For updates to an existing file, prepend a short **What's New** section above the Summary.

## Sizing

- Aim for the `max_lines_soft_cap` from config (default 300 lines).
- If the topic genuinely needs more, split supplementary detail into a research file and link it.
- If the topic is narrow, a shorter file is fine. Do not pad.

## Slug collisions

If two topics normalize to the same slug, append a numeric suffix: `topic-slug-2.md`. The run progress log should note the disambiguation.
