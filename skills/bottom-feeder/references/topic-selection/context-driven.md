# context-driven

Primary topic selection method. Mine the workspace's existing context — not generic seed lists.

## Why

Generic seeds produce encyclopedias. Context-driven selection produces decision support documents tied to real people, real projects, and real deadlines.

## Sources to Mine (priority order)

1. **Project management** — Asana, Linear, Jira, GitHub Issues
   - Active tasks, blocked items, upcoming milestones
   - Each initiative or epic is a potential topic
   - Blocked items are high-value — research WHY something is blocked

2. **Team conversations** — Slack, Discord, Telegram, daily logs
   - Repeated themes, explicit asks, unresolved questions
   - Score boost when mention count >= 2 or time-sensitive
   - Mine `memory/daily/YYYY-MM-DD.md` (today + yesterday)
   - Extract candidate topics from direct asks like "research X", "build a plan for Y", or "we keep tripping on Z"

3. **Existing knowledge** — `knowledge/`, `memory/`
   - Topics with stale dates (>14 days old in rapid-change domains)
   - Topics referenced but without a file yet
   - Broken cross-references
   - If no file exists, or only shallow notes exist, mark it as a knowledge gap
   - If a strategic or recently accessed file is older than 14-30 days in a fast-moving domain, mark it as a refresh candidate

4. **Company docs** — Google Docs, Notion, Confluence
   - Strategy documents needing research backing
   - Meeting notes with unresolved action items
   - Roadmap items needing competitive research

5. **User/team profiles** — `memory/contacts/`, USER.md
   - What is each team member working on?
   - Where are they overloaded? What knowledge helps them most?

## Scoring

**Topic Score = Urgency × Impact × Knowledge Gap**

- **Urgency:** deadline or blocker? (High = this week, Medium = this month, Low = this quarter)
- **Impact:** how many people/decisions informed? (High = whole team, Medium = one dept, Low = one person)
- **Knowledge Gap:** how much do we NOT know? (High = no coverage, Medium = stale, Low = recent + strong)

High on all three → goes first.

## Staleness Check

Before finalizing any candidate:
- Search `knowledge/` by keyword/slug
- No file or only shallow notes → high-value gap, prioritize
- File exists but >14 days old in rapid-change domain → refresh candidate
- Coverage strong and fresh → skip, pick next

Refresh candidate format:
- topic
- existing_file
- staleness_reason

## Trending Signals

Light trend scan to propose additional candidates:
- Web headlines via any search tool
- Recent community chatter in relevant channels
- Prefer topics intersecting configured interests
- Avoid pure hype — cap to 1 trending pick per run

Trending candidates should answer "why this matters here" before they are allowed into the queue. If the only reason is hype, skip it.

## Tip

Prefer topics you can map to a specific person or team who will use the output. General-interest topics that serve the whole org are still valid — don't discard them just because there's no single owner.
