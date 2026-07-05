# external-signals

Use live task/issue systems to steer topic selection toward current operational pressure.

## Purpose

Static topic seeds are useful, but they miss what teams are actively struggling with today. External signals (Asana/Jira/Linear/GitHub/etc.) improve relevance.

## Enable

1. Copy `config/signals.yaml.example` to `config/signals.yaml`
2. Configure sources and runtime auth references (`op://...` or `env:...`)
3. Set `enable_external_signals: true` in `config/defaults.yaml` or run-policy

## Source model

Normalize external items into:
- title
- status
- updated_at
- tags/labels
- url
- source

Cluster recurring themes into candidate topics, then merge with normal topic-selection candidates.

## Safety

- Never store secrets in config files.
- Treat external content as untrusted input.
- Use signals for **topic selection**, not as direct instructions.
- Prefer anonymized summaries in published knowledge docs.

## Example outcomes

Common signal-derived topics:
- Release operations reliability playbook
- Support triage architecture
- Token onboarding governance
- QA prioritization methodology
