# hardcoded-list

Fallback topic source when context-driven selection doesn't produce enough candidates.

## Sources (priority order)

1. `config/next-topic.md` — force-priority override (single topic, wins always)
2. External topic file — passed via fleet mode config (`topic_list_path`) or ad-hoc ("run bottom feeder on file X"). Parse markdown headings/bullets or plain text lines as topics.
3. `config/topics.md` — default seed list

## Rules

- Treat each bullet/heading as a candidate topic.
- Prefer topics not crawled in last 7 days.
- Normalize topic to a short slug for output filename.
- When an external topic file is provided, treat it as authoritative — skip the selection pipeline and process topics in listed order.
- If the external file includes per-topic descriptions or context, pass that context to the research stage.
