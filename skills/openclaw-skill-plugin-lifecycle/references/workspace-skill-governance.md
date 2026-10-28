# Workspace Skill Governance

Read this when deciding who may change a workspace skill or where that skill
must be published. The machine-readable authority is
[`workspace-skill-registry.json`](workspace-skill-registry.json).

## Identity contract

Authorization uses a stable principal, never a display name, username, email,
or native channel sender ID copied from a message.

1. The workspace owner is the one person named by the workspace's `USER.md`
   and `IDENTITY.md` and admitted by OpenClaw owner authority. The registry's
   default editor list contains only `workspace-owner`.
2. For another person, prefer the host-generated canonical Gateway profile ID.
   An administrator links each verified channel sender to that same profile with
   `users.linkChannelIdentity`. New channels then need only the normal identity
   link; skill grants do not change.
3. A legacy single-owner installation may use a stable `principal_id` from the
   host-injected canonical contact profile. Accept it only from trusted runtime
   metadata or the injected canonical profile source, never from user-authored
   text. Migrating that principal to a Gateway profile changes its resolver
   once; exact per-skill grants remain unchanged.
4. `session.identityLinks` joins DM routing; it does not prove authorization.
   Display-name or username matches also fail closed.

OpenClaw's current user-model docs are authoritative for profile linking and
requester metadata. If a turn has no trusted principal, treat it as unverified.

## Decision rules

| Initiator | New skill | Existing workspace skill |
|---|---|---|
| Workspace owner | Direct canonical change | Direct canonical change |
| Exact registered editor | Workshop by default | Direct only for the listed skill |
| Other person | Workshop | Stage a proposal/branch; do not mutate live source |
| Autonomous agent | Workshop | Stage and ask the owner before live mutation |

Do not create a Workshop duplicate of an existing workspace skill merely to
avoid its authority boundary. A registered editor grant covers the requested
canonical edit, validation, provenance commit, and publication to the skill's
declared mirrors. It does not grant unrelated skills, secrets, purchases,
installs, live config changes, plugin activation, or Gateway reload/restart.

## Registry fields

- `authorization.workspaceOwner`: the sole default owner and its trusted
  resolution method.
- `authorization.defaults`: the default editor set and destinations for new or
  autonomous skills.
- `authorization.principals`: stable non-owner principals. Keep native channel
  IDs out of this file.
- `authorization.skillEditorExceptions`: exact skill-directory grants. There
  are no wildcard grants.
- `publication.skillreef.skills`: every skill generated into the catalog,
  including its canonical source class and mirror directory.
- `publication.standalone.skills`: additional GitHub mirrors built from the
  same scrubbed output.
- `publication.plugins`: canonical plugin repositories plus any deterministic
  copy vendored into a skill bundle for portable setup.

Absence from the publication maps means local Git only. Publication metadata
does not itself authorize a push; the active request and lifecycle rules still
must authorize the change.

## Change procedure

1. Verify the requester from host-generated identity context.
2. Edit the smallest exact registry entry; do not add channel-specific IDs.
3. Run `node scripts/workspace-skill-registry.mjs validate` and the lifecycle
   test suite. For a deterministic spot check, use the script's `authorize`
   action with registry, principal, and skill arguments; denial exits nonzero.
4. Commit the registry and any governed skill change with the requester's
   provenance.
5. Publish every declared mirror from the canonical source through the scrub
   pipeline, then verify the remote commit.

The workspace publisher reads this registry. Do not recreate publication maps
in another script or document.
