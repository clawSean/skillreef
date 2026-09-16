# Domain Backlink Audit

Run this only when installing, migrating, or adding web-facing domain skills.
Routine web tasks do not need it.

Each installed domain skill that can reach a web surface must backlink to
`web-use` while retaining its own data, account, action, and approval policy.
The portable audit checks the currently known skill names and ignores ones that
are not installed:

```bash
bash scripts/audit-domain-backlinks.sh
```

Pass explicit directory names to check a different installation:

```bash
bash scripts/audit-domain-backlinks.sh linkedin food-ordering custom-domain
```

For each failure, add an ownership sentence equivalent to:

> Load `web-use` for generic transport selection, browser context, provider
> fallback, attachment proof, and not-blocked escalation. This domain skill
> retains account, data, action, and approval policy.

Do not copy provider state, credentials, or account details into `web-use`.
