# Personal campaign safety and qualification

The v5 quick path is a bounded **requested-route coding screen**, not a universal
model comparison, an OS sandbox, or a production adoption gate.

## Preparation

1. Use public or synthetic fixtures only. Keep credentials, private conversation,
   memory and production delivery out of tasks and public artifacts.
2. Stage a new, deliberately authored JSON config inside the evidence run directory.
   Never copy a production config or auth store. Pin its SHA-256 in each route's
   `auth_preparation`. There is no automatic credential export.
3. Use an explicit unused `ws://127.0.0.1:<port>` Gateway endpoint, never `18789`.
   Runtime HOME, state and workspaces are disposable; evidence stays in the run
   directory. A fresh run directory is required after any attempted campaign;
   this path does not resume or retry attempted cells.
4. Use the conservative config shape enforced by
   `scripts/personal_campaign_config.py`: local loopback Gateway, no-auth only
   within that trusted disposable loopback environment, reload/UI disabled,
   no channels, plugins/browser/cron disabled, no discovery or update traffic,
   and model catalog refresh disabled. Unknown fields, includes, environment
   imports, arbitrary paths, external services and literal API credentials fail.
5. Declare the provider endpoint structurally in `models.providers`, not in a
   comment. The narrow profile admits one explicitly configured provider with
   requested model IDs and no fallback; the current campaign uses one shared
   prepared config. Cross-provider credentials/config composition is not proven.
   A provider-free config uses a loopback endpoint and `mock-only` dummy key.
   API preparation references only `${CLAWGAUGE_ISOLATED_API_KEY}`; provide it
   through an approved protected credential mechanism, never a chat transcript.
6. Restrict tool names to the coding/file surface. `tools.fs.workspaceOnly: true`
   narrows file tools; **host shell execution is not OS containment**. Disposable
   roots and environment/config checks prevent accidental production targeting,
   not malicious shell access. Do not run adversarial or private tasks here.
7. Before live inference, validate the config and perform an isolated native
   Gateway startup/create/delete/cleanup qualification while checking that
   production config hash/mtime and agent roster are unchanged. Fake lifecycle
   tests and `openclaw config validate` do not satisfy this native runtime gate.
   Confirm provider plugins/runtime prerequisites without installing or changing
   production policy. If the prepared profile cannot boot the exact route, stop.
8. Qualify each exact route with a non-scoring cell before the frozen 18-cell
   matrix. Subscription handoff is not implemented; no paid API/provider/account
   substitution is authorized merely because the requested route is blocked.

## Evidence limits

- Three coding/repo tasks × three repetitions × two routes, serial,
  counterbalanced, no automatic retries. Cell deadline <=180 seconds, campaign
  deadline <=4200 seconds, with bounded termination grace additional to deadlines.
- Whole-result memoization is disabled at harness entry. This is different from
  provider prefix/KV caching; no cache-normalized speed claim follows.
- Native aggregate results remain untouched. Receipts bind the scheduled cell,
  native result and frozen inputs. Keep failed outputs and logs; infrastructure
  failures make the matrix incomplete, while genuine quality failures remain
  evidence rather than disappearing from the denominator.
- Only model/provider are submitted by the native quick-path harness. Other
  requested control fields are frozen intent, **not observed or enforced route
  proof**. Reasoning, fast state, account, effective model and fallback require
  separate qualification. The strict tier has no independent observer and blocks.
  Frozen quality floors record intent; this screen does not grant an adoption or
  value verdict from them. Use the full evidence comparator for that decision.
- Missing token/cost provenance is `n/a`, not zero; native schema defaults do not
  establish observed usage. Estimated cost is not billed cost. No hard dollar cap
  is claimed: use the fixed workload, deadlines and a declared soft estimate.
- Config admission and mock/native-schema regression passes prove only their
  stated boundaries. They do not prove real-provider startup, subscription
  availability, tool isolation, benchmark quality, or model superiority.

## Regression commands

Run from the skill root:

```sh
python3 scripts/test_personal_campaign_config.py
python3 scripts/test_personal_campaign.py
python3 scripts/self_test.py
```

ShellBench-dependent checks require its existing pinned Python environment;
report an explicit skip if absent rather than installing dependencies or claiming
that the integration passed. Retain raw private proof under `runs/<run-id>/`.
Publish the scrubbed source only; no local run directories or operator configs.
