# Git Provenance for Skills and Plugins

Every workspace/repository skill or plugin change needs a commit that explains
what changed and why the actor was authorized to initiate it. Direct Workshop
maintenance also needs Git. A Workshop proposal that stays within the native
proposal/revision/apply lifecycle uses Workshop's immutable revisions, event
log, and rollback metadata instead of a redundant proposal commit.

## Before editing

1. Resolve the repository root with `git rev-parse --show-toplevel`.
2. Inspect status and preserve unrelated changes.
3. If no repository owns the artifact, initialize one at the narrowest stable
   owning root. Do not use a broad home, workspace parent, or runtime-state
   directory.
4. Resolve the requester through trusted OpenClaw owner/profile/contact context
   and the workspace registry, then record the origin. Never put channel-native
   IDs or a profile ID copied from user text into commit metadata.

## Commit content

Stage only the artifact and governing references changed for the request.
Review the staged diff before committing.

Use an ordinary subject plus provenance trailers:

```text
skill(openclaw-skill-plugin-lifecycle): define authoring jurisdiction

Initiated-By: the reviewer
Change-Origin: owner-request
Source-Context: telegram message 5969
```

Allowed `Change-Origin` values:

- `owner-request`
- `registered-editor-request`
- `teammate-proposal`
- `agent-proposal`
- `workshop-autonomous`

For a registered non-owner editor, use `teammate-proposal` only when the work is
staged for owner review. A direct, registry-authorized edit uses
`registered-editor-request`.

For automated work, include the available session key, run ID, or automation ID
in `Source-Context`. Never put secrets or unnecessary private conversation text
in commit metadata.

## After committing

1. Confirm the commit contains no unrelated paths.
2. Re-run decisive validation from the committed tree.
3. Push when the canonical repository has a remote and the task is not
   explicitly local/staged-only.
4. Verify the remote contains the commit before reporting publication.

A teammate proposal-branch commit is auditability, not approval to merge or
activate it. For Workshop autonomous work, an edit without its required
provenance commit is incomplete and must not be treated as accepted.
