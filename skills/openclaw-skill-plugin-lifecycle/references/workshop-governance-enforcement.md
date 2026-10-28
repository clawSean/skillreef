# Workshop Governance Adapter Setup

Use this when an operator wants autonomous Skill Workshop reviews to receive the
same lifecycle and workspace-skill registry as foreground authoring.

## Canonical adapter

- Repository: <https://github.com/EdgeClaws/openclaw-workshop-governance>
- Plugin ID: `workshop-governance-context`
- Registry contract: `workspace-skill-registry.json` schema version 1

The plugin reads the lifecycle skill and configured governance references from
the active agent's canonical workspace on every targeted review. A workspace
may use this bundle's combined registry or separate authority and publication
registries. The plugin injects them, plus a compact index of current workspace
skills, into detached experience reviews and the weekly Workshop collection
review. It does not copy policy into plugin source, change Workshop mode, or
start another model review.

This is a model-governance adapter, not a filesystem ACL. Git history, Workshop
proposal records, ordinary tool policy, and operator review remain the recovery
and audit boundaries.

## Install for another operator

Installing or activating a plugin and restarting a Gateway require that
operator's explicit authorization.

1. Install this lifecycle skill in the agent's canonical workspace.
2. Customize `references/workspace-skill-registry.json`; keep the owner default
   singular and link collaborator channels to durable Gateway profiles.
3. Clone or pin a reviewed adapter release in a durable directory outside the
   OpenClaw package installation.
4. Link-install the plugin from that checkout:

   ```sh
   openclaw plugins install --link --force .
   ```

5. Merge the following shape into the existing config without replacing other
   plugin paths, allowlist entries, or plugin settings:

   ```json5
   {
     plugins: {
       load: { paths: ["/absolute/path/to/openclaw-workshop-governance"] },
       allow: ["workshop-governance-context"],
       entries: {
         "workshop-governance-context": {
           enabled: true,
           hooks: { allowConversationAccess: true },
           config: {
             lifecycleSkillPath:
               "skills/openclaw-skill-plugin-lifecycle/SKILL.md",
             governanceReferencePaths: [
               "skills/openclaw-skill-plugin-lifecycle/references/workspace-skill-registry.json"
             ]
           }
         }
       }
     }
   }
   ```

6. Run the adapter's `npm test` and `npm pack --dry-run`, then run
   `openclaw config validate` and inspect the plugin runtime.
7. Activate with the narrowest supported reload. Restart only when reload is
   unavailable or fails and the operator explicitly authorizes it.
8. Prove one bounded Workshop review contains the adapter marker, current
   lifecycle text, and registry. A loaded plugin receipt alone is not prompt
   delivery proof.

Keep Workshop in `propose` or `off` until the lifecycle skill's direct-auto Git
and recovery gates pass. The adapter does not make `auto` safe by itself.
