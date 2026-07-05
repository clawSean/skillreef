# Mermaid Skill — Local Notes (Sean's VPS)

Environment-specific gotchas found in practice. Check here before rendering.

## Rendering: point mmdc at system Chrome (REQUIRED on this host)

`mmdc` (puppeteer) looks for a bundled Chrome under `~/.cache/puppeteer` that is **not installed** here → fails with `Could not find Chrome (ver. ...)`. The box has a working system Chrome at `/usr/bin/google-chrome`. Point puppeteer at it:

```bash
PUPPETEER_EXECUTABLE_PATH=/usr/bin/google-chrome \
  mmdc -i input.mmd -o output.png -b white -w 1700 \
  -p ~/.openclaw/workspace/skills/mermaid/references/puppeteer-config.json
```

(Do **not** `npx puppeteer browsers install` — install actions need approval; pointing at the existing Chrome is the right fix.)

## Authoring gotchas

- **`<br/>` works in NODE labels but NOT subgraph titles.** A `<br/>` in a `subgraph X["..."]` title renders the second line *overlapping* the subgraph content (clipped/hidden). Keep subgraph titles **single-line and short**; for multi-line detail use a child node inside the subgraph instead.
- **Long single-line subgraph titles get truncated** to the subgraph's measured width. Keep them short; push detail into nodes or the surrounding prose.

## Delivery

- **Telegram `message(media=...)` rejects `/tmp` paths** ("not under an allowed directory"). Render or copy into the workspace (e.g. `artifacts/`) before sending.
- **Chat preview:** render PNG with `-b white` (transparent reads badly on Telegram dark mode).
- **GitHub docs:** prefer inline ` ```mermaid ` fences in markdown (GitHub renders natively, stays editable, no binary) over committing a rendered image.

*Last updated: 2026-06-17 — gotchas found rendering the lobster-boilerplate single-gateway architecture diagram.*
