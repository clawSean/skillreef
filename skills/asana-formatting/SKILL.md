---
name: "asana-formatting"
description: "Format Asana HTML, task titles/bodies, comments, mentions, and provenance."
---

# Asana Formatting

Use this skill before any Asana write where text quality or rich-text rendering matters.

This skill does not authenticate to Asana and does not send API requests. Pair it with the local Asana API/MCP skill or tool for the actual write.

## Core Rules

- Asana rich text is HTML, not Markdown.
- Rich text must be a valid HTML fragment wrapped in one root `<body>` tag.
- Use `html_notes` for rich task/project descriptions.
- Use `html_text` for rich comments/stories/status updates.
- Use plain `notes` or `text` only when the payload should be unformatted plain text.
- Escape literal `&`, `<`, and `>` inside text content.
- Keep markup compact. Avoid blank-line padding and stray whitespace nodes.

Example:

```html
<body><strong>Summary</strong><ul><li>One item</li></ul></body>
```

## Before Writing

1. Decide whether the destination expects rich HTML or plain text.
2. Normalize task titles into the house title shape from `references/task-writing.md`.
3. For task descriptions, keep the body short: `Overview/Motivation`, `Ask`, and optional `Supporting Docs/Links`.
4. For comments, use real block tags for headings and lists. Do not fake headings with inline bold.
5. Include provenance when the write should remain traceable.
6. If a user mention must notify someone, add the user as assignee/follower as appropriate; rich-text mention links alone may not notify.

## Field Map

| Asana target | Plain field | Rich field |
|---|---|---|
| Task description | `notes` | `html_notes` |
| Story/comment | `text` | `html_text` |
| Project description | `notes` | `html_notes` |
| Project status/brief | n/a | `html_text` |
| Team description | n/a | `html_description` |

## Reference Files

Read only what the task needs:

- `references/rich-text.md` - supported tags, spacing, lists, tables, links, mentions, and HTML validation rules.
- `references/task-writing.md` - concise task body and title normalization rules.
- `references/provenance.md` - trace footer fields and rich-text footer templates.

## Output Discipline

When drafting content for a future Asana write, show the exact field and value that should be sent, for example:

```json
{
  "html_text": "<body><h2>Update</h2><p>Short update.</p></body>"
}
```

If the write will be performed immediately through an API tool, silently apply these rules and send the valid field/payload shape.
