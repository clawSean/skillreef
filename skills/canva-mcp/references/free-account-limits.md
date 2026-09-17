# Canva Free + MCP limits

## Live-proven baseline

A bounded gateway-owned Free-account smoke test successfully generated four
design jobs, exported six PDFs, opened and cancelled five draft transactions,
and read ten designs. It saw no rate-limit, credit, license, or quota error.
This proves ordinary collaboration flows; it does not prove unlimited volume.

## Published request limits

| Lane | Published rate |
|---|---:|
| Create / generate | 20/min |
| Start / commit edit transaction | 20/min |
| Editing operations | 50/min |
| Reads | typically 100/min |
| Export | 20/min |

Canva does not publish a Free-plan total quota for ordinary MCP docs, edits, or
exports. AI generation can consume Canva credits, so do not treat it as an
unlimited Free production lane. The Connect API documents a conservative
ceiling of 500 exports per user per 24 hours.

## Failure map

| Symptom | Cause | Response |
|---|---|---|
| 429/rate limit | Minute ceiling | Wait 60 seconds; batch or back off |
| Credit/quota error during generation | AI credit allowance | Use an existing design/manual edit or wait for reset |
| license_required | Premium asset | Replace with a free or uploaded asset |
| Export format error | Unsupported or paid format | Call get-export-formats; use a returned regular format |
| Plan/eligibility error | Paid/Enterprise feature | Use basic workflow; Bulk Create is Enterprise-only |
| Authorization error | OAuth expired or revoked | Reconnect the gateway-owned Canva MCP |

## Official sources

- [Canva MCP tools and limits](https://www.canva.dev/docs/mcp/tools/)
- [Canva MCP usage policy](https://www.canva.dev/docs/mcp/usage-policy/)
- [Connect API export limits](https://www.canva.dev/docs/connect/api-reference/exports/create-design-export-job/)
