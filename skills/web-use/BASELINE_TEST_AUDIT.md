# Baseline Test Audit - web-use

## Scope

Baseline structural checks for the local `web-use` skill.

## Current Checks

Run:

```bash
bash skills/web-use/scripts/test.sh
```

The test script verifies:

- frontmatter name matches `web-use`
- Browserless extraction helper parses and exposes `--help` without credentials
- Browserless session helper parses and exposes `--help` without credentials
- Browserless media-request helper parses and exposes `--help` without credentials
- TinyFish helper parses and exposes `--help` without optional dependencies

Credentialed live extraction tests are intentionally not part of baseline because
they consume external service credits and depend on target-site behavior.
