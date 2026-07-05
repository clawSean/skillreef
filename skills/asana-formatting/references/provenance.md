# Asana Write Provenance

Every Asana write should carry enough traceability that a later reader can answer:

- Who asked for this?
- Where did it come from?
- In what mode was it done?
- On whose authority?
- Which agent performed it?

Applies to:

- Task creates
- Task updates
- Comments/stories
- Status updates
- Project changes
- Cron/background writes
- Manual agent-assisted writes

Capture fields when available:

- Requester or human owner
- Source surface: Telegram, Slack, cron, CLI, email, etc.
- Source message/link/request id
- Mode: `draft`, `approved`, `automation`, or `background`
- Approval state/evidence
- Run/session id
- Agent identity

Where to put it:

- Existing task updates: prefer an Asana comment/story.
- New task creates: provenance may go in the body only when useful, but keep it as a compact footer.
- Do not bloat task bodies with provenance dumps.

Normal plain trace footer:

```text
trace: <requester> via <surface> (<link/id>) | <draft|approved|automation|background> | <agent>
approval: <who + link, if relevant> | run: <run/session id, if any>
```

Rich-text rendering rule:

- Wrap routine trace footers in `<blockquote>`.
- Italicize the trace line with `<em>`.
- Use `|` pipes as separators.
- Do not use a loud `Provenance` heading for routine comments.
- Reserve `<hr/>` for long, multi-section comments only.

Canonical rich trace footer:

```html
<blockquote><em>trace: <requester> via <surface> (<link/id>) | <draft|approved|automation|background> | <agent></em></blockquote>
```

For background or automation records where a human is unlikely to read the comment inline, a labeled provenance block is acceptable:

```text
Provenance
Source: cron (<job-name>) | Mode: background | Agent: <agent>
Run: <run/session id> | Requester: scheduled (owner: <owner>)
```

## Practical Templates

Formatted task body:

```html
<body><h2>Overview/Motivation</h2><p>Short problem or business context.</p><h2>Ask</h2><p>Short, concrete request.</p><h2>Supporting Docs/Links</h2><ul><li><a href="https://example.com">Relevant link</a></li></ul></body>
```

Formatted comment:

```html
<body><h2>Update</h2><p>Short summary of what changed.</p><ul><li><strong>Decision:</strong> concise decision text.</li><li><strong>Next step:</strong> concise next step.</li></ul><blockquote><em>trace: <requester> via <surface> (<message id>) | approved | <agent></em></blockquote></body>
```

Compact plain task body:

```text
Overview/Motivation
Short problem or business context.

Ask
Short, concrete request.

Supporting Docs/Links
- Relevant link
```