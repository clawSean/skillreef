# Asana Task Writing

Use these rules when creating or rewriting Asana task titles and descriptions.

## Task Body Policy

Keep task bodies concise. Default to exactly these sections:

```text
Overview/Motivation
<1-4 short lines explaining the problem, user need, or business reason>

Ask
<1-4 short lines stating what needs to be decided, designed, investigated, or built>

Supporting Docs/Links
<optional bullets or links only when they materially help>
```

Rules:

- Keep each section short and scannable.
- Prefer product/user language over engineering implementation language unless the task is explicitly engineering-only.
- Preserve intent, not wording.
- Remove duplicated context, filler, and hedge phrases.
- If technical detail is uncertain, omit it rather than anchoring the task to a bad assumption.
- If supporting material exists, link it instead of summarizing it at length.
- Include a local brand marker only when the workspace style asks for one; do not put brand markers in titles unless explicitly requested.

Avoid in normal task bodies:

- Code-level suggestions.
- File names, function names, class names, method names.
- Repo-specific implementation proposals.
- Architecture guesses that engineers must verify later.
- Pseudo-code.
- Stack-specific instructions unless the task is explicitly about that stack.
- Long copied research notes.
- Dev-only terminology that non-engineers do not need.
- Intake-form sections such as `Requirements`, `Expected Result`, `Actual Result`, `Reproducibility`, `Branch`, `Version`, `Build`, `OS`, or `Device Type`, unless the task is explicitly a QA bug intake that must retain them.

Rewrite direction:

- Verbose bug/report form -> compress to user problem + ask.
- Researched implementation brain dump -> compress to motivation + ask + links.
- Dev-specific proposal -> rewrite into product outcome language when possible.

## Task Title Policy

When creating or renaming Asana tasks, normalize the title into this shape:

```text
[Primary noun phrase] - [Short declarative title]
```

Goal:

- Make titles easy to scan in list and board views.
- Lead with the most useful domain label.
- Keep the suffix short, specific, and non-conversational.

Choose the left side using the shortest stable noun phrase that identifies the task. Prefer:

1. Specific feature, screen, or flow: `Authorize Device`, `Transaction List`
2. Specific integration, vendor, or external system: `Moonpay`, `Intercom`
3. Specific chain, asset, or protocol: `SOL`, `XMR`, `TON`
4. Specific subsystem or product area: `Swap`, `Earn`, `Notifications`
5. Specific repo, module, or code surface: `accb`, `reports`, `RN`, `Devops`
6. The most concrete object being changed: `Login Flow`, `Quote Engine`, `Seed Phrase`

Left-side rules:

- Prefer narrower, recognizable buckets over broad generic ones.
- Use the object/domain, not the action.
- Do not use vague labels like `Bug`, `Issue`, `Task`, or `Fix`.
- Combined forms are allowed when useful, such as `Swap (Ramps) - Ignore balances for quoting`.

Right-side rules:

- Describe the issue, deliverable, or change compactly.
- Prefer noun/action labels over sentence fragments.
- Keep it short enough to scan quickly.
- Avoid conversational titles, full sentences, filler words, vague verbs, and multi-clause titles.

Examples:

- `Coinrank - V3 API`
- `HyperEVM - Transaction Sync`
- `Authorize Device - Redesign`
- `SOL - Rent Calculation`
- `Gift Cards - Bitrefill Fallback`
- `Intercom - Native Chat Integration`
- `Notifications - Missing Password Reminder`
- `Import - Autocomplete Seed Phrase`
- `Transaction List - Categorize Fee Txs`
- `Swap (Ramps) - Ignore balances for quoting`

Rewrite examples:

- `Can we fix SwapKit stuff` -> `SwapKit - Quote fallback`
- `Need to update authorize device flow` -> `Authorize Device - Redesign`
- `Investigate why SOL rent is weird` -> `SOL - Rent Calculation`
- `Review Changelly integration for swaps` -> `Swap - Review Changelly integration`

Before sending any create/update request to Asana, silently normalize the title unless the user explicitly says to preserve the original title.