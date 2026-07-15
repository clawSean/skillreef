# crusty-contributor Roadmap

Future improvements for the upstream-contribution workflow. Keep these as adoption notes until they are proven locally and folded into `SKILL.md` or a repo overlay.

## Review Skill Adoption

### Peter / steipete references

- `steipete/agent-scripts`: https://github.com/steipete/agent-scripts
- `steipete/agent-scripts` changelog entry: `2026-05-22 - Auto Review Skill`
- `steipete/agent-scripts` symlink: `skills/autoreview` -> `../../agent-skills/skills/autoreview`
- Source skill: `openclaw/agent-skills/skills/autoreview`
- Related Peter workflow: `steipete/agent-scripts/skills/github-project-triage` says to run Codex Auto Review before commit/land unless the change is trivial/docs-only or explicitly skipped.

### Scope call

`autoreview` is broadly applicable to non-trivial development work, but the first Sean adoption point should be upstream PR closeout through `crusty-contributor`.

Why here first:

- Upstream PRs already require public-safe proof, CI follow-through, and maintainer-facing polish.
- A structured second-model review is most valuable before commit, push, PR update, or re-review requests.
- The contributor skill already owns PR readiness language and avoids saying "merge-ready" before CI/bots/review agree.

Do not immediately make it mandatory for all development work. Promote it through `development-orchestration` only after the helper is installed or vendored locally, smoke-tested on a small branch, and the runtime cost/latency tradeoff is understood.

### Candidate integration

Add a closeout gate after focused tests and before commit/push for non-trivial PR branches:

1. Freeze scope: original issue/request, target branch, changed files, intended behavior, owner boundary.
2. Run `autoreview` on the branch diff, usually Codex default first.
3. Verify every accepted finding by reading the real code path.
4. Fix only in-scope blockers; classify adjacent findings as follow-up.
5. Rerun focused tests and review when a review-triggered fix changes code.
6. Record accepted/rejected findings in local notes or PR evidence only when useful to maintainer review.

Skip for docs-only, typo-only, formatting-only, or tiny low-risk changes unless the user asks for a second review.

### Open questions

- Install path: workspace skill copy from `openclaw/agent-skills`, project-local vendored copy, or referenced checkout under `~/projects/agent-skills`.
- Engine defaults on Sean's VPS: Codex default vs Claude/Fable optional lane, considering local memory pressure and model capacity.
- Whether ClawSweeper/Mantis proof requests should trigger `autoreview` automatically before asking for re-review.
- Whether development-wide adoption belongs in `development-orchestration` as an optional closeout lane after the contributor pilot.
