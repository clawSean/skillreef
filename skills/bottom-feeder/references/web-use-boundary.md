# Web-use boundary

Bottom Feeder is a research **orchestrator**, not a web-provider router.

## Bottom Feeder owns

- topic selection and prioritization;
- research direction and evidence requirements;
- orchestration mode, batching, checkpoints, and recovery;
- synthesis, quality gates, provenance, and durable knowledge writes.

## `web-use` owns

- public search and known-URL fetching;
- cited-research specialist selection;
- browser context and authenticated/stateful browser workflows;
- public extraction/scraping provider selection;
- local browser-app and shared-tab escalation;
- provider capability proof, fallback, and not-blocked escalation.

Before collection, Bottom Feeder chooses the **source category** needed by the
topic. Load `web-use/SKILL.md`; then load only the narrow reference required by
that category. Do not hard-code Brave, Perplexity, Browserless, TinyFish, a
browser app, or an “all tools” ladder in this skill.

If a domain skill is active, it owns domain intent, account context,
credentials, and action/approval policy. `web-use` supplies transport and
fallback mechanics without overriding those domain rules.

Generation-model fallback in `config/defaults.yaml` or an explicitly supplied
run policy is separate from web collection routing.
