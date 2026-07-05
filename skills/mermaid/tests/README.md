# Mermaid Skill Tests

Small deterministic test suite for the Mermaid skill.

Run from the skill directory or workspace root:

```bash
~/.openclaw/workspace/skills/mermaid/tests/run_tests.sh
```

Covers:

- `mmdc` availability/version
- `render_mermaid.sh` shell syntax and executable bit
- root-safe Puppeteer no-sandbox config
- missing-input failure path
- simple fixture render to PNG
- representative examples documentation

No network calls, package installs, or OpenClaw restarts.
