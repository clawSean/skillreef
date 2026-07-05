# completion-checklist

Before advancing to the next topic, verify the current topic's output passes ALL checks:

## Required sections (knowledge/topics file)
- [ ] Summary — ≥2 sentences (aim for 3 on broad topics), no placeholders
- [ ] Current State — concrete facts with dates, not vague
- [ ] Why It Matters — tied to the user's ecosystem/work, not generic
- [ ] Open Questions — at least 1 genuine unknown
- [ ] Sources — at least 2 dated sources (URL + date accessed)

## Required metadata (YAML header)
- [ ] `confidence` set to low/medium/high
- [ ] `sources_used` lists actual tools used
- [ ] `crawled` timestamp present
- [ ] `mode` set (routine|burn)

## Run-policy gates (if active)
- [ ] Provider lock/fallback constraints were respected
- [ ] Provider rotation events (if any) logged in run-progress
- [ ] Topic status in run-progress matches disk state

## Quality gates
- [ ] No unresolved TODO/TBD placeholders
- [ ] If confidence is low, reason is explicitly stated
- [ ] File is self-contained for a new reader

## Failure behavior
- If a section can't be completed: mark `[INCOMPLETE: reason]`
- Do not silently skip topic; partial + honest > missing output
- Log gaps and retries in run-progress file
