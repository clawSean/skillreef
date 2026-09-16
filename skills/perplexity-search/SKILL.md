---
name: "perplexity-search"
description: "Use Perplexity Agent API for cited research by depth."
---

# Perplexity Research

Use Perplexity for cited web research when independent source discovery or
specialized multi-step research improves the answer. Keep the primary agent responsible for
the final interpretation.

## Route by research depth

| Need | Preset | Command |
|---|---|---|
| Everyday cited research; light multi-step lookup | `low` | `bash scripts/ask.sh "question"` |
| Multi-hop comparison or broad source aggregation | `medium` | `bash scripts/reason.sh "question"` |
| Expert-level analysis or exhaustive source coverage | `high` | `bash scripts/research.sh "question"` |
| Large evidence-backed collection with per-item research | `wide-research` | `bash scripts/wide-research.sh "question"` |
| Open-ended, long-running, tool-heavy investigation | `xhigh` | `bash scripts/xhigh.sh "question"` |

Use `low` only when heavier modes are unnecessary. Prefer `medium` when
reasoning across sources matters and `high` when completeness materially
matters. Use `xhigh` only when the user explicitly wants maximum effort or the
task genuinely needs sustained agentic work.

Perplexity also offers a `fast` preset, but native `web_search`/`web_fetch` own
single-fact and known-page retrieval here. Do not add or spend a Perplexity call
for that redundant lane unless a task explicitly requires Perplexity output.

## Workflow

1. Frame one focused research question and run the narrowest sufficient preset;
   completion means the response contains a substantive answer and source list.
2. Treat the result as a research analyst's packet, not final authority. The primary agent
   synthesizes the user-facing answer and resolves material contradictions.
3. Inspect cited primary sources when a claim is consequential, surprising,
   disputed, or about to drive action. Do not mechanically verify every
   citation on routine low-risk use.
4. Pair Perplexity with local knowledge or another search lane when an
   independent source set materially improves confidence. Avoid duplicate calls
   for the same question.
5. Report uncertainty when sources disagree or the Agent API returns no usable
   search results.

## Prompt and API posture

The scripts use Perplexity's official Agent API at `POST /v1/agent` with dynamic
presets. Dynamic presets preserve Perplexity's tuned search/reasoning
configuration and automatically receive quality improvements.

Do not add a top-level `instructions` field: with a preset it replaces the
preset's tuned system prompt. Put task-specific synthesis requirements in the
user input instead. Do not impose tight output-token caps on reasoning presets;
they can consume the cap before producing useful text.

The shared runner asks for:

- a direct answer before detail;
- primary and authoritative sources where practical;
- clear separation of sourced facts, inference, and uncertainty;
- inline citations plus a compact source list;
- no filler or unsupported certainty.

## Credentials

Never store key material in source or output. The runner accepts either:

1. `PERPLEXITY_API_KEY` supplied by the runtime; or
2. `PERPLEXITY_1PASSWORD_REF`, resolved with `op read` at runtime.

For named local profiles, copy `references/credentials.local.example.sh` to
`references/credentials.local.sh` and map profile names to 1Password references.
The populated local file is private and never published. There is no automatic
profile failover; select one deliberately with `PERPLEXITY_KEY_PROFILE`.

## Failure handling

- `401`: selected key is invalid or expired.
- `402`: selected project is out of credits.
- `429`: rate limited; wait before retrying.
- HTTP `200` with `status: failed|cancelled|incomplete`: treat as failure and
  show the bounded provider error.
- Empty answer or source list: retry only when the task still warrants the
  spend; otherwise use another research lane and state the limitation.

## Verification

Run `bash scripts/test.sh` for offline structure and parsing checks. After a key
change or migration, run one bounded `low` request and confirm a completed answer
plus sources. Do not spend calls proving every preset unless a preset-specific
failure appears.

## Official references

- Agent API migration: https://docs.perplexity.ai/docs/agent-api/migrate-from-sonar/overview
- Presets: https://docs.perplexity.ai/docs/agent-api/presets
- Agent API reference: https://docs.perplexity.ai/api-reference/agent-post
- Official migration skill: https://github.com/perplexityai/api-platform-developers/tree/main/skills/migrate-sonar-to-agent-api
