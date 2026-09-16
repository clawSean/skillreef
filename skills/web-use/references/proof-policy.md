# Capability Proof Policy

Provider configuration, installation, credentials, and historical success are
not current capability proof.

## Admission

- `proven` requires current runtime discovery plus one representative bounded
  live task for the claimed lane.
- Record exactly what passed, what did not, runtime/version when relevant, date,
  and durable evidence source.
- Scope admission narrowly: public extraction proof is not authenticated-session
  proof; app launch is not page control; tab registration is not page access.
- Treat profile, login, tab attachment, display, provider balance, and process
  state as volatile and recheck before sensitive/authenticated work.

## Regression

Downgrade a provider immediately when a representative runtime or task proof
fails for a durable reason. A transient timeout may receive one bounded retry;
otherwise change state/provider/category rather than preserving a green label.

## Local evidence

Current-machine evidence belongs in the private `proof-ledger.local.md` and
`provider-registry.local.md`. Those files must never be published or copied to
another agent as portable truth. Each installation builds its own ledger.
When absent, seed them from `proof-ledger.local.example.md` and
`provider-registry.local.example.md`; never populate an example with live state.
