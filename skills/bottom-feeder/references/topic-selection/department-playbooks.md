# department-playbooks

Generate department-specific operational playbooks that show each team lead exactly how AI can help their daily work.

## Why This Matters

Generic knowledge files inform. Department playbooks **activate.** They answer: "What does this mean for ME, specifically, on Monday morning?"

## Structure for Each Playbook

1. **The Problem** — What is this person/department struggling with? (Pull from project management data)
2. **Current Task Load** — Live snapshot of their actual tasks (from Asana/Linear/Jira)
3. **Specific Workflows** — 4-6 concrete workflows the AI agent can execute for them
   - Each workflow: trigger → what the agent does → what the human reviews → time saved
4. **Time Savings Estimate** — Conservative hours/week saved per workflow
5. **How to Start** — First task to try this week (lowest friction, highest proof-of-value)

## Workflow Design Rules

- Every workflow must name the **specific tool or data source** the agent uses
- Every workflow must specify what the **human still does** (review, approve, refine)
- Never claim the agent replaces the person — it handles the operational load so they focus on judgment
- Include estimated time: current state vs with agent

## Example Departments

- **Engineering** — Code review pre-check, architecture docs, dependency scanning, CVE triage
- **QA** — Test case generation, regression risk assessment, build monitoring, Maestro flow creation
- **Growth/Marketing** — Sprint capacity planning, competitive research, content calendar, campaign briefs
- **Support/Ops** — Article drafting, ticket pattern analysis, training guide creation, chatbot content
- **Security** — Bug bounty triage, CVE monitoring, incident response runbooks
- **Product** — Competitive intelligence, feature prioritization (RICE), spec drafting, analytics interpretation

## When to Generate

Department playbooks are highest value when:
- A team is adopting AI for the first time (proof of concept)
- A key person is overloaded and needs leverage
- A role is being created or transitioning (e.g., QA → PM)
- A function was orphaned (e.g., security lead departed)

## Quality Gate

A department playbook passes quality gate when:
- [ ] Names a specific person as the audience
- [ ] Includes their actual current tasks (not generic)
- [ ] Each workflow specifies trigger, agent action, human review step
- [ ] Time savings estimates are conservative (not aspirational)
- [ ] "How to Start" section has one concrete action for this week
