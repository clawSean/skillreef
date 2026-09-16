# Web Decision Matrix

Choose category before provider. Rows are mutually clarifying, not mandatory
sequential attempts.

| Question | Yes | No / next |
|---|---|---|
| Does local knowledge or a prior proof already answer it? | use narrow local source | continue |
| Does a domain skill/API own authoritative structured data or action policy? | load domain skill; it may leapfrog generic web | continue |
| Is this public discovery/current fact-finding? | native search; fetch primary sources | continue |
| Is the URL known and readable without JS/login? | native fetch | continue |
| Does it require cited synthesis, comparison, multi-hop reasoning, breadth, or completeness? | specialist cited research | continue |
| Does it require JS, rendering, interaction, upload/download, or local persistent login? | managed browser | continue |
| Is it protected public data, bulk crawl, or repeated structured extraction? | hosted/public extraction | continue |
| Does it genuinely need a full visible local browser/app context? | local provider registry + live canary | continue |
| Did the user request their current/shared tab, need to watch, or require exceptional sensitivity? | shared-tab context, pinned | continue |
| Is the needed surface browser chrome, a native app, or an OS dialog? | GUI/computer use after display preflight | continue |
| Is the remaining step human-only or approval-gated? | visible handoff | classify the exact unhandled gap |

## Specialist leapfrogs

- Domain API over generic search when it is authoritative and fit-for-purpose.
- Perplexity over ordinary search when synthesis quality/source breadth is the
  task, not merely URL discovery.
- Managed browser directly when known JS/auth interaction is required.
- Hosted extraction directly when a known public anti-bot/bulk workload matches
  a proven provider and no login is involved.

## Retry budget

Retry once only when failure evidence is transient or stale-state specific. Then
change state, provider, or category. Never loop identical calls because the
cheapest provider exists.

## Terminal outcomes

- **Completed:** result verified at the intended state.
- **Handoff:** exact human-only step stated; agent resumes afterward.
- **Blocked:** all relevant proven lanes exhausted or authority/risk forbids
  continuation; exact evidence and next possible unlock stated.
- **Unavailable capability:** provider is disabled, uninstalled, or unproved;
  do not collapse this into overall task blockage.
