# Local Provider Registry — Template

Copy this file to `provider-registry.local.md` on each installation. Record only
current local state; never publish the populated copy.

| Category | Priority | Provider/profile | Admission | Availability | Last proof | Constraints / next check |
|---|---:|---|---|---|---|---|
| Native retrieval | 10 | example | candidate | unknown | none | Confirm tool discovery and bounded fetch |
| Managed browser | 10 | example | candidate | unknown | none | Confirm profile, login scope, snapshot, control |
| Hosted extraction | 10 | example | candidate | unknown | none | Confirm credential, balance, privacy boundary, public smoke |
| Local visible app | 10 | example | candidate | unknown | none | Confirm installed app, profile, display, capture/control |
| Shared tab | 10 | example | candidate | unknown | none | Confirm consent, pairing, attachment, snapshot/control |
| GUI/computer use | 10 | example | candidate | unknown | none | Confirm unlocked display and permissions |

Admission states: `proven`, `configured-unproven`, `candidate`, `unavailable`,
or `retired`. Availability is separately `available`, `degraded`, `offline`,
`human-gated`, or `unknown`. Priority is a positive integer; lower values win
only within the same category and only after fit/proof gates. Leave numeric
gaps for contained insertion. Scope proof narrowly and link its ledger entry.
