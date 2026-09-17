---
name: "canva-mcp"
description: "Canva MCP create, edit, export, and Free-account capability checks through gateway-owned OAuth."
---

# Canva MCP

1. Verify the gateway-owned `canva` MCP connection is authorized before work. Do not substitute a Codex-bound connector or third-party wrapper.
2. For a new design, use Canva's create/generate flow and turn the selected candidate into an editable design before editing. Warn that generation may use Canva AI credits.
3. Read a design before editing. Start a transaction, make the requested changes as a draft, show the result, and commit only after the user explicitly approves. Cancel unapproved drafts.
4. Call `get-export-formats` before every export and pass only a supported format. Return the export URL.
5. Treat Free-plan entitlements as task-specific until live-proven. Use [Free account limits](references/free-account-limits.md) to distinguish published request-rate ceilings from unknown total quotas.
6. Batch routine work and respond to errors by cause: retry `429` after a minute; replace premium assets on `license_required`; use a listed regular export format; re-authenticate the gateway connection if authorization fails.
7. Keep volume probes bounded: use candidates or a clearly named throwaway design, test no more than 10 calls per lane unless the user asks to target a published ceiling, and clean up only with recoverable user-approved actions.

## Verification

- Record operation count, elapsed time, success/failure responses, and actual quota/error codes in a task evidence file.
- Say “rate limit observed” only after an actual rate-limit response. Say “Free total unknown” when Canva has not published or exposed a total allowance.
