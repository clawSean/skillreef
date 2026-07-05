# quality-score

Use after synthesis and before final write. This complements `references/quality-gate/completion-checklist.md`.

## Scorecard

Score each dimension 0–2:

- **Completeness**: required sections present, no vague placeholders
- **Evidence**: sources are dated, credible, and sufficient for claims
- **Novelty / delta**: adds new value beyond existing local knowledge
- **User relevance**: tied to JPop/OpenClaw/Edge/product system, not generic
- **Actionability**: has decisions, watch items, next steps, or implementation hooks
- **Safety / provenance**: untrusted content separated from conclusions; risky claims labeled

Total: 12 points.

## Pass thresholds

Routine mode:
- pass: ≥8/12
- retry once: 5–7/12
- write partial: ≤4/12

Burn/deep/tree-search mode:
- pass: ≥10/12
- retry once: 7–9/12
- write partial: ≤6/12

## Retry behavior

On retry, change at least one of:
- source mix
- query framing
- branch question
- recency window
- model/provider, if run policy allows

Do not repeat the same search and hope for better output.

## Output note

Add a small footer or run-log entry:

```text
Quality score: 10/12
Weak spots: evidence availability, open questions
Follow-up: revisit when new sources appear
```

For user-facing artifacts, keep scoring concise. Full scoring belongs in `knowledge/.runs/<date>-<mode>.md`.
