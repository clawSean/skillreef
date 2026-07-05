# Skill Reef 🪸🦞

A growing catalog of reusable OpenClaw skills.

## Vision

See `VISION.md` for the repo direction. Short version: skills should be useful
at response time, self-contained enough to copy, and grounded in verified command
shapes instead of pointer chains.

## Included skills

- `asana-formatting` - Asana rich-text HTML, task title/body style, comments, mentions, and provenance footers.
- `bottom-feeder` - Knowledge crawling and note synthesis for durable topic/research files.
- `brain-swap` - Fleet-wide OpenClaw model switching across config, sessions, and cron jobs.
- `claude-foreman` - Dispatch heavy coding work to Claude CLI while OpenClaw orchestrates.
- `interactive-sessions` - Design and operate button-driven Telegram/Slack chat sessions, games, wizards, polls, and guided workflows.
- `knowledge-search` - Local semantic knowledge-base search with ChromaDB + Ollama.
- `mermaid` - Mermaid diagram authoring and rendering workflow.
- `moltmaster` - Controlled OpenClaw OAuth/auth-profile refresh operations with dry-run, backups, and provider guardrails.
- `pdf-to-markdown` - Convert PDFs to Markdown with Docling.
- `plugin-creator` - Create, design, review, and troubleshoot OpenClaw plugins, slash commands, message presentation buttons, and interactive handlers.
- `ralph-wiggum` - Bounded iteration loop for small projects and prototypes with verification after each slice.
- `shell-swap` - Mass-switch OpenClaw model settings with codex/gpt/claude lane aliases.
- `shop-agent` - Browser-driven Amazon/retailer shopping: search, compare, price-check, add to cart, and walk checkout — always stopping for human approval before purchase. Pairs with `web-use` for product/price data and browser context.
- `shrimp` - Internal pass-through helper for `/shrimp` sub-agent dispatch.
- `telegram-ui` - Telegram rich chat UI patterns: inline buttons, polls, edits, replies, reactions, media, and pins via OpenClaw. Includes live-verified authoring rules for OpenClaw's experimental `richMessages` mode (see below).
- `web-use` - Front-door routing for web search, fetch, extraction, protected backends, and real browser context.

## ⚡ Heads-up: OpenClaw `richMessages` changes Telegram rendering semantics

OpenClaw ships with Telegram `richMessages` **off** by default. Turning it on
unlocks tables, collapsible `<details>` blocks, math, checkbox lists, and inline
media — but it also **breaks every newline-based formatting habit**:

- Plain newlines, blank lines, `•` bullets, and markdown `-`/`1.` lists all
  collapse into run-on text. The rich renderer treats whitespace like a browser.
- Structure must come from explicit HTML blocks: `<p>` per paragraph,
  `<ul>/<ol>` + `<li>` for lists, `<br>` for forced breaks (never `<br/>` —
  the self-closing form gets escaped to literal text).
- Empty `<p></p>` spacers are collapsed too. To get a real blank line between
  paragraphs, use a paragraph holding a non-breaking space: `<p>&#160;</p>`.

All of this is live-verified on iOS (2026-07-05) and documented with the full
rendering matrix and house authoring rules in `skills/telegram-ui/SKILL.md`.
If your agent's Telegram messages suddenly render as one giant run-on wall
after enabling rich mode, this is why.

## Companion kits

- `x-twitter-kit` - X/Twitter access stack for OpenClaw: bundled Peeper no-credit public-account monitoring, xAI/Grok `x_search`, `xurl` OAuth setup, diagnostics, and posting safety. Canonical repo: https://github.com/clawSean/openclaw-x-twitter-kit

Companion kits are indexed here for discovery but keep their source in their
own repos when they carry larger docs, tests, fixtures, or setup flows.

## Notes

- This repo contains the public-safe subset of the local custom skill library.
- Skills with environment-specific secret references or sensitive local bindings are intentionally omitted.

## Structure

```text
skills/
  <skill-name>/
    SKILL.md
    references/
    scripts/
```

Each skill lives in its own directory so it can be copied or installed cleanly into an OpenClaw workspace.
