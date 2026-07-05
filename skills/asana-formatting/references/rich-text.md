# Asana Rich Text

Asana rich text uses HTML fragments. Markdown may render literally or poorly in task notes and comments.

## Required Shape

Wrap rich text in one root `<body>` tag.

```html
<body><strong>Summary</strong><ul><li>One item</li></ul></body>
```

Escape literal XML characters in text content:

- `&` -> `&amp;`
- `<` -> `&lt;`
- `>` -> `&gt;`

Unescaped XML characters can invalidate the entire rich-text payload.

## Common Tags

Commonly useful tags:

- `<body>`
- `<strong>` for bold
- `<em>` for italic
- `<u>` for underline
- `<code>` for inline monospaced text
- `<ol>`, `<ul>`, `<li>` for lists
- `<a>` for links and Asana object mentions
- `<blockquote>` for quotes or trace footers
- `<pre>` for preformatted text
- `<hr/>` for major dividers
- `<table>`, `<tr>`, `<td>` for simple tabular content

Tasks and project briefs may support additional structure such as `<h1>`, `<h2>`, `<hr/>`, and `<img>`. Project briefs may support tables and some embedded objects. If rendering behavior matters, test on a disposable task/comment first.

## Comments

Use `html_text` for formatted Asana comments.

Headings:

- `<h1>` and `<h2>` render in comments in tested workspaces.
- Prefer `<h2>` for normal comment section headings.
- Reserve `<h1>` for a single top-level title when truly needed.
- Do not use standalone inline `<strong>` as a heading. Inline tags do not create line breaks.

Lists:

- Nested unordered lists render correctly.
- Nested ordered lists render hierarchically.
- Mixed ordered/unordered lists render correctly.
- Inline `<strong>`, `<em>`, and `<code>` work inside list items.

Spacing:

- Blank lines in `html_text` can create large vertical gaps.
- Keep markup compact.
- Do not pad blocks with extra blank lines or stray whitespace nodes.
- Let block tags such as `<h2>`, `<ul>`, `<ol>`, `<pre>`, and `<blockquote>` create spacing naturally.

Dividers:

- `<hr/>` renders cleanly but is visually heavy.
- Use `<hr/>` only for major section breaks, not routine trace footers.

Quotes:

- `<blockquote>` renders with an indented vertical bar.
- Inline formatting survives inside blockquotes.

Preformatted blocks:

- `<pre>` preserves line breaks, multiple spaces, monospace styling, and escaped tag text.
- Use `<pre>` for fixed-width alignment or copied technical text.

Tables:

- `<table>`, `<tr>`, and `<td>` can render as visible grid columns.
- Inline `<strong>`, `<em>`, `<code>`, and `<a>` work inside cells.
- Keep table cells to inline content, links, and normal text.
- Do not put `<pre>` directly inside `<td>` unless the target workspace has accepted it in testing.
- Wide explicit cell widths may become horizontally scrollable in narrow task panes.
- Use tables sparingly because narrow cells wrap heavily and can become tall.

Nesting limits:

- Do not nest `<h1>`, `<h2>`, `<blockquote>`, or `<pre>` inside list items.
- Do not put lists inside headers, blockquotes, or pre blocks.
- Unsupported nesting can reject the entire payload.

## Links And Mentions

API-created rich-text mentions do not necessarily notify by themselves. When notification matters, assign the user or add the user as a follower.

Mention link shape:

```html
<a data-asana-type="user" data-asana-gid="USER_GID">@Name</a>
```

Asana object links can preserve metadata such as:

- `data-asana-type`
- `data-asana-gid`
- `data-asana-dynamic`
- `data-asana-accessible`

Canonical task-link shape for trace footers:

```html
<a href="https://app.asana.com/1/<workspace-gid>/project/<project-gid>/task/<task-gid>" data-asana-gid="<task-gid>" data-asana-accessible="true" data-asana-type="task" data-asana-dynamic="true">Task Name</a>
```