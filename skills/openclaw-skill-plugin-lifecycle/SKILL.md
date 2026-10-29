---
name: openclaw-skill-plugin-lifecycle
description: Required before any OpenClaw skill, plugin, extension, reusable procedure, or durable authoring-package creation, update, publication, audit, or retirement.
---

# OpenClaw Skill + Plugin Lifecycle

Load this skill before changing any skill, plugin, extension, reusable
procedure, or durable authoring package. It owns governance and provenance;
specialized creator skills own implementation details.

## Working principles

- Prefer the smallest useful artifact and the shortest process that proves the
  requested outcome. Do not overengineer routine authoring.
- Prioritize usability and delivered value. Handle recoverable friction as part
  of the work instead of inventing approval gates or blockers.
- Treat edge cases in proportion to demonstrated risk. Preserve real safety,
  authority, privacy, and recovery constraints, but do not let speculative or
  nuanced edge cases prevent reasonable progress.
- Reuse a proven owner or implementation before adding another abstraction.
- These principles are not exhaustive. Every change or proposal must also
  follow the current `SOUL.md`, `USER.md`, `IDENTITY.md`, `AGENTS.md`, relevant
  contact/group/project records, active conversation instructions, and the
  artifact owner's requirements.

## 1. Classify and locate the owner

Read [authoring governance](references/authoring-governance.md). When requester
authority or publication applies, also read [workspace skill governance](references/workspace-skill-governance.md)
and its machine-readable
[registry](references/workspace-skill-registry.json). Then choose the smallest
reusable artifact and its canonical source:

- **Procedure:** operational guidance that should not trigger as a capability.
- **Repository/workspace skill:** a skill in a normal Git checkout, including
  this workspace's `skills/` tree.
- **Workshop skill:** a skill inside the active agent's `workshop-skills/` tree.
- **OpenClaw plugin:** runtime code adding tools, commands, handlers, providers,
  channels, hooks, or UI.
- **Codex plugin:** a Codex plugin package and marketplace entry.
- **Project unit:** multi-session state owning several related artifacts.

Search the likely owner, neighboring skills/plugins, installed OpenClaw docs,
and pending Workshop proposals before creating another identity. One behavior
gets one authoritative owner; references point to it instead of copying rules.

## 2. Resolve authority, then route by initiation

The sole default workspace owner is the person declared by `USER.md` and
`IDENTITY.md` and admitted by OpenClaw owner authority. Do not infer ownership
from a display name or channel-native ID. Resolve non-owner requesters through a
trusted principal as defined by the registry; unknown identity fails closed.

### Workspace-owner-led work

The workspace owner controls every live skill or plugin outside
`workshop-skills/`. Apply the requested change directly to the canonical source,
verify it, commit it, and publish every declared registry target. Do not add a
second approval gate or a Workshop proposal for repository-owned work.

For an owner-requested Workshop change, use the current Workshop lifecycle and
finish the requested live outcome unless the owner asks for audit-only or
proposal-only work.

### Registered-editor work

An exact `skillEditorExceptions` entry permits that verified principal to update
only the named workspace skill. The grant includes the canonical edit,
validation, provenance commit, and declared publication mirrors. It does not
authorize another skill, install, live config change, plugin activation, or
Gateway reload/restart.

### Other teammate-led work

- **New skill:** create it in the requester's Workshop collection by default.
- **Existing workspace/repository skill:** do not mutate the live artifact and
  do not create a duplicate Workshop skill. Stage a complete suggestion through
  the owning repository's branch/PR workflow, or a clearly labeled committed
  proposal artifact when no branch workflow exists. Record the requester and
  notify the workspace owner for the authority decision.
- **Existing Workshop skill:** apply only after checking the request against
  owner expectations, the complete current Workshop set, pending proposals,
  and adjacent non-Workshop skills. Reject or consolidate conflicts and verify
  accepted changes.

### Agent-initiated work

- **New skill:** create or propose it only in Workshop under the configured
  mode. A human editor exception never grants an autonomous agent that person's
  authority.
- **Existing artifact outside Workshop:** stage the suggestion and ask the
  workspace owner before live mutation.
- **Existing Workshop skill:** autonomous maintenance is permitted under the
  configured Workshop mode and the direct-auto Git gate below.

## 3. Use the correct implementation guide

- **Skills:** use the active `skill-creator` guidance for structure and quality;
  repository-owned skills use normal file/repository tools.
- **Workshop:** read the installed docs under
  `~/.npm-global/lib/node_modules/openclaw/docs/tools/skill-workshop/`
  and use `skill_workshop` for proposals; never hand-edit proposal storage.
  For autonomous-review policy delivery, read
  [Workshop governance adapter setup](references/workshop-governance-enforcement.md).
  Its installable adapter is vendored under
  `assets/workshop-governance-plugin/`; the shared repository remains the
  editable upstream and the vendor lock prevents drift.
- **OpenClaw plugins:** use the focused references in this bundle, then inspect
  current installed docs and SDK declarations. Start with
  [manifest/build](references/openclaw-plugin-manifest-build.md); load
  [command/buttons](references/telegram-command-buttons.md),
  [branching feasibility](references/button-branching-feasibility.md), or the
  [one-shot implementation prompt](references/one-shot-extension-prompt.md)
  only when that branch applies.
- **Codex plugins:** use Codex's system `plugin-creator` skill. This is separate
  from OpenClaw plugin authoring.

Use installed docs/source as runtime authority when copied examples drift. Do
not treat generated mirrors, caches, installed bundles, or scrubbed public
copies as canonical editable sources.

## 4. Workshop safety gates

Workshop `propose` mode stages pending proposals. Workshop `auto` mode permits
new background reviews to edit the Workshop tree directly and permits a newly
created foreground repair proposal to be applied immediately. Changing the mode
does not apply the existing pending backlog.

Do not enable or rely on Workshop `auto` until all are true:

1. Every nonempty live `workshop-skills/` tree that the configured autonomous
   mode can edit is Git-backed.
2. Every autonomous edit path demonstrably creates a provenance-bearing commit.
3. Live skills and pending proposals have been checked for conflicts/duplicates.
4. Recovery from Git history has been tested.

Stock direct maintenance has no proposal rollback snapshot, post-turn scanner,
complete edit history, or automatic Git commit. The governance adapter can
supply the Git gate only when its `autoCommitProvenance` option is explicitly
enabled and proven against the live Workshop repository. Workshop proposal
revisions, events, and apply rollback metadata are sufficient audit records for
proposal-only work; they do not replace Git for direct `auto` maintenance.
Until the direct-auto gates pass, keep autonomous mode at `propose` or `off`.
Never change the mode as a side effect of authoring work.

For proposal updates, read the complete live skill first. The proposal must be
the complete intended next `SKILL.md`, not an essay about the change. Inspect,
evaluate when useful, apply only within the initiation rules above, and compare
the live result byte-for-byte with the intended content.

## 5. Verify the artifact

Use checks proportional to the artifact:

- skill: validate frontmatter, trigger routing, references, scripts, overlap,
  and `openclaw skills check`;
- OpenClaw plugin: validate manifest/package identity, current SDK types, build,
  discovery/load path, focused tests, and the real interaction path when
  authorized;
- Codex plugin: use the Codex plugin validator and required development
  cachebuster/reinstall flow;
- procedure: confirm callers point to one current authority.

For evidence-led skill optimization, read
[skill optimization audit](references/skill-optimization-audit.md). Inspect the
final diff and exclude unrelated dirty-tree changes. Valid frontmatter alone
does not prove sound ownership, non-conflict, or behavior.

Authoring or publishing does not authorize installs, dependency changes, live
config mutation, plugin enablement, Gateway reload/restart, or external sends.
Follow `USER.md` and the active task's authority for those actions.

When authorized runtime activation is needed, prefer a supported, bounded hot
reload and verify the new generation actually loaded. Restart only when hot
reload is unavailable or fails and the active task explicitly authorizes the
restart; never report disk state as live runtime state.

## 6. Commit and publish with provenance

Every workspace/repository skill or plugin change requires a Git commit. A
Workshop proposal that remains in the proposal lifecycle uses Workshop's own
immutable revisions and event provenance; direct Workshop maintenance requires
Git. Read [Git provenance](references/git-provenance.md) before committing.

- Publish every surface declared for the skill in the
  [workspace registry](references/workspace-skill-registry.json), unless the
  active requester limits the task to local/staged work. An unlisted skill stays
  local after its provenance commit.
- If no repository owns the canonical source, initialize one at the narrowest
  stable owning root before editing.
- Never mix unrelated working-tree changes into the commit.
- Record whether the change was owner-requested, teammate-proposed,
  agent-proposed, or Workshop-autonomous.
- Publish skills/plugins only through the no-drift and scrub rules in
  `knowledge/procedures/code-publishing.md`.

Done means the live/staged state matches its authority boundary, validation
passes, a provenance commit exists, and every required remote contains it.
