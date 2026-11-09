# Telegram Rendering Guardrails

Read when composing Telegram prose, headings, literal bullets, or code. The
main skill owns delivery-path choice; these are strict, route-specific syntax
boundaries. Do not apply them to captions or legacy-HTML sends.

## Structure and spacing

- **On the calibrated `message` rich-text path:** give each authored prose
  break one empty visual row with source-adjacent `<br><br>`; plain `\n\n` is
  not a visual separator. On ordinary finals, use native blocks or concise prose.
- On a calibrated break path, pick each separator by boundary:
  - `heading/block ↔ body`: real source blank line for syntax only; rely on the
    block's native spacing and do not add `<br><br>`.
  - `prose → prose`: `First.<br><br>Next paragraph.`
  - `literal list → prose`: `Last item.<br><br>Next paragraph.`
  - `literal item → literal item`: the list-wide density below.
- Multiple headings are fine; each starts at start or after real `\n\n`.
  Never put `<br><br>` before a heading, even with source blank lines between
  the tags and `###`: the heading can render literally and the gap compounds.
  End the prior block with a real source blank line instead. Keep `<br><br>`
  away from block-level HTML islands.
- In calibrated rich `message` sends, keep each prose break source-adjacent to
  `<br><br>`. Ordinary finals may use source blank lines for Markdown structure,
  not visual spacing.
- On a break-canary path, separate literal `•` rows with the density rule's
  inline breaks; bare source newlines can collapse and are never separators.
  On ordinary finals, use semantic Markdown or HTML lists, not literal rows.
  Never use one `<br>` for prose or block boundaries, standalone `<br><br>`,
  or spacer entities.
- Use literal `•` prose/status rows with inline breaks only on a calibrated
  `message` route. Reserve semantic lists for nesting, tasks, runtime
  requirements, **and ordinary finals**.
- Literal lists are compact by default. If every item is **90 visible characters
  or fewer**, use one source-adjacent `<br>` between items. If any item exceeds
  90, use `<br><br>` between every item. Count rendered characters, including
  spaces but excluding formatting syntax and URL destinations. This predicts
  wrapping beyond two mobile lines.

## Scanability exceptions

- Native `###` headings need one real source blank line before body text for
  syntax. Never add `<br>` to a heading or prefix one with `<br><br>`.
- Never use inline code for newline/escape-sequence examples: these leaked backticks
  in a client canary. Use prose or fenced code.
- These are composition rules, not a license to rewrite arbitrary outbound
  text. A global newline multiplier would alter code, lists, tables, headings,
  and captions; a global break-tag remover would alter intentional examples.
