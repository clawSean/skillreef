#!/usr/bin/env bash
set -euo pipefail

skill_dir="$(cd "$(dirname "$0")/.." && pwd)"
workspace_dir="$(cd "$skill_dir/../.." && pwd)"
skill_file="$skill_dir/SKILL.md"
vendor_dir="$skill_dir/assets/workshop-governance-plugin"
vendor_script="$skill_dir/scripts/workshop-governance-plugin-vendor.mjs"
failures=0

check() {
  local label="$1"
  shift
  if "$@"; then
    printf 'PASS: %s\n' "$label"
  else
    printf 'FAIL: %s\n' "$label"
    failures=$((failures + 1))
  fi
}

rejects() {
  if "$@"; then
    return 1
  fi
  return 0
}

in_dir() {
  local dir="$1"
  shift
  (cd "$dir" && "$@")
}

check "SKILL.md exists" test -s "$skill_file"
check "required lifecycle name" grep -q '^name: openclaw-skill-plugin-lifecycle$' "$skill_file"
check "description makes loading mandatory" grep -q '^description: Required before any OpenClaw skill' "$skill_file"
check "governance reference exists" test -s "$skill_dir/references/authoring-governance.md"
check "git provenance reference exists" test -s "$skill_dir/references/git-provenance.md"
check "optimization reference exists" test -s "$skill_dir/references/skill-optimization-audit.md"
check "workspace governance reference exists" test -s "$skill_dir/references/workspace-skill-governance.md"
check "workspace registry exists" test -s "$skill_dir/references/workspace-skill-registry.json"
check "Workshop adapter setup exists" test -s "$skill_dir/references/workshop-governance-enforcement.md"
check "Workshop adapter vendor exists" test -s "$vendor_dir/openclaw.plugin.json"
check "Workshop adapter vendor lock exists" test -s "$skill_dir/references/workshop-governance-plugin.lock.json"
check "workspace registry validates" node "$skill_dir/scripts/workspace-skill-registry.mjs" validate
check "Workshop adapter vendor lock verifies" node "$vendor_script" verify
check "Workshop adapter vendor tests pass" in_dir "$vendor_dir" npm test
check "Workshop adapter package dry-run passes" in_dir "$vendor_dir" npm pack --dry-run
check "workspace owner may edit any skill" node "$skill_dir/scripts/workspace-skill-registry.mjs" authorize "$skill_dir/references/workspace-skill-registry.json" workspace-owner home-control
check "registered editor may edit exact shopping skill" node "$skill_dir/scripts/workspace-skill-registry.mjs" authorize "$skill_dir/references/workspace-skill-registry.json" person:example-collaborator shop-agent
check "registered editor is denied an unlisted skill" rejects node "$skill_dir/scripts/workspace-skill-registry.mjs" authorize "$skill_dir/references/workspace-skill-registry.json" person:example-collaborator home-control
check "skill preserves practical authoring preferences" grep -q 'Do not overengineer routine authoring' "$skill_file"
check "skill routes to SOUL preferences" grep -q 'SOUL.md' "$skill_file"
check "skill routes to USER preferences" grep -q 'USER.md' "$skill_file"
check "skill routes to IDENTITY preferences" grep -q 'IDENTITY.md' "$skill_file"
check "lifecycle owns direct workspace-owner edits" grep -q 'workspace owner controls every live skill' "$skill_file"
check "lifecycle supports exact registered editors" grep -q 'skillEditorExceptions' "$skill_file"
check "lifecycle defaults new teammate skills to Workshop" grep -q 'create it in the requester.*Workshop collection' "$skill_file"
check "registry keeps one default owner" grep -q '"workspaceSkillEditors"' "$skill_dir/references/workspace-skill-registry.json"
check "lifecycle gates every affected Workshop tree" grep -q 'Every nonempty live `workshop-skills/` tree' "$skill_file"
check "lifecycle prefers verified hot reload" grep -q 'prefer a supported, bounded hot' "$skill_file"
check "obsolete feedback authority removed" test ! -e "$workspace_dir/memory/feedback/auto-apply-skill-workshops.md"

if [[ -f "$workspace_dir/knowledge/procedures/code-publishing.md" &&
      -f "$workspace_dir/scripts/publish-skillreef.sh" ]]; then
  check "AGENTS routes directly to lifecycle skill" grep -q 'skills/openclaw-skill-plugin-lifecycle/SKILL.md' "$workspace_dir/AGENTS.md"
  check "AGENTS covers Workshop self-creation" grep -q 'Workshop self-creation is permitted and encouraged' "$workspace_dir/AGENTS.md"
  check "legacy procedure points to lifecycle skill" grep -q 'skills/openclaw-skill-plugin-lifecycle/SKILL.md' "$workspace_dir/knowledge/procedures/skill-optimization-audit.md"
  check "publishing procedure points to lifecycle skill" grep -q 'skills/openclaw-skill-plugin-lifecycle/SKILL.md' "$workspace_dir/knowledge/procedures/code-publishing.md"
  check "development router points to lifecycle skill" grep -q 'skills/openclaw-skill-plugin-lifecycle/SKILL.md' "$workspace_dir/skills/development-orchestration/SKILL.md"
  check "publisher reads canonical registry" grep -q 'workspace-skill-registry.json' "$workspace_dir/scripts/publish-skillreef.sh"
  plugin_checkout="$(node "$skill_dir/scripts/workspace-skill-registry.mjs" plugin-checkout "$skill_dir/references/workspace-skill-registry.json" workshop-governance-context)"
  if [[ -d "$plugin_checkout/.git" ]]; then
    check "Workshop adapter vendor matches upstream" node "$vendor_script" check "$plugin_checkout"
  else
    printf 'SKIP: upstream Workshop adapter checkout unavailable\n'
  fi
else
  printf 'SKIP: private workspace integration checks (portable bundle)\n'
fi

while IFS= read -r ref; do
  check "referenced file $ref exists" test -f "$skill_dir/$ref"
done < <(grep -oE 'references/[A-Za-z0-9._/-]+\.md' "$skill_file" | sort -u)

while IFS= read -r ref; do
  check "referenced registry $ref exists" test -f "$skill_dir/$ref"
done < <(grep -oE 'references/[A-Za-z0-9._/-]+\.json' "$skill_file" | sort -u)

check "no malformed headings" test -z "$(grep -nE '^#{1,6}[^#[:space:]]' "$skill_file" || true)"

exit "$failures"
