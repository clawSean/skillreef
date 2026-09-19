# EdgeApp PR Proof Packet

Copy the useful sections beneath the target repository's existing PR template.
Delete empty or irrelevant headings. Keep secrets, private sources, local-only
paths, raw logs, and sensitive account details out of the public packet.

## Proof

### Revision and scope

- Head: `<full SHA>`
- Base: `<branch and SHA/date>`
- Risk / state: `<R0-R4>` / `<not_required|planned|attempted|satisfied|blocked_external|stale>`
- Owning layer: `<GUI|login UI|core|currency|exchange|native|server>`
- User claim: `<one sentence>`
- Preserved behavior / non-goals: `<one sentence>`

### Focused evidence

- Positive: `<command, count/result, environment, what it proves>`
- Closest negative: `<command, result, wrong behavior excluded>`
- Regression discrimination: `<old failure, mutation, golden/vector, or rationale>`
- Repository gates: `<type/lint/format/diff/full check and result>`

### Runtime or artifact evidence

- Route: `<unit|built bundle|simulator|device|native|provider|server|other>`
- Configuration/input: `<real|fake|stubbed|forced|synthetic; sanitized>`
- Artifact: `<sanitized link/path or N/A>`
- Direct inspection: `<expected state seen; forbidden state absent>`
- Cleanup/redaction: `<completed/result>`

### Compatibility and lifecycle

- Platforms/devices: `<covered and skipped>`
- Lifecycle: `<start|restart|logout/login|network loss|cancellation|repeat|N/A>`
- Dependency matrix: `<old/old, old/new, new/old, new/new, or N/A>`
- Provider/live boundary: `<covered, blocked, or N/A>`

### Known gaps

- `<unproven matrix cell, blocked route, synthetic limitation, or none>`

### Remaining non-proof gates

- CI: `<status/classification>`
- Product/API decision: `<exploratory candidate|selected; owner/status or none>`
- Security/privacy review: `<owner/status or none>`
- Migration/release/maintainer/canonical-path gate: `<status or none>`

### Freshness declaration

- `<Evidence is bound to the full head above; prior evidence is stale or explicitly rebound after unchanged-blob verification.>`
