# Evidence-Led Skill Optimization

Use this branch when a skill repeatedly fails, over-triggers, misses clear
requests, grows stale/duplicative, or needs evidence before publication. This is
an audit method, not a separate source of authoring jurisdiction.

## Inputs

- canonical skill source and owner;
- 2–5 representative success, failure, or correction traces;
- held-out checks or a concrete observable failure;
- scripts, references, dependencies, permissions, and publication surfaces.

If meaningful validation cannot be constructed, stop at a recommendation. Do
not rewrite a skill from vibes or expand one incident into a universal rule.

## Workflow

1. Record the current version/hash and invocation route.
2. Classify the evidence: missing trigger, wrong trigger, missing procedure,
   stale fact, duplicated owner, unsafe side effect, or context bloat.
3. Find the smallest edit that addresses the demonstrated failure while
   preserving unrelated behavior.
4. Check security, authority, privacy, tool scope, portability, and context cost.
5. Run held-out checks against baseline and candidate when practical.
6. Accept only when the failure is fixed or evidence improves without a material
   regression; otherwise reject the edit and preserve the finding outside the
   live skill.
7. Follow the lifecycle skill's jurisdiction, commit, validation, publication,
   and activation rules.

## Acceptance criteria

Accept when the target behavior improves, important cases remain intact, the
trigger is no broader than needed, and the skill stays lean. Reject edits that
only add explanation, dump transcripts, flatten distinct workflows, or weaken
safety/authority boundaries.

For a noisy pending Workshop backlog, audit proposals separately; do not treat
mode changes, queue size, or proposal cleanliness as approval to apply them.
