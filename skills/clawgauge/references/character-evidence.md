# Character evidence contract

OpenClaw's current built-in character scenarios, `character-vibes-gollum` and
`character-vibes-c3po`, test persona commitment, conversational naturalness,
funniness, coherence, and completion of a small file task. They do **not** test
general intent inference. ClawGauge therefore labels this layer
`persona-naturalness` and keeps intent/autonomy claims out of its verdicts.

Character judging is subjective secondary evidence. It cannot rescue a failed
task, safety gate, or deterministic benchmark result.

## Required attestation

An upstream `character-eval-summary.json` does not independently prove the
scenario revision, transcript completeness, observed judge route, reasoning
mode, provider family, or blind-label mapping. Before comparison, add a
ClawGauge attestation under `clawgaugeAttestation`, or provide the same object in
a sidecar with `--attestation`.

The required schema is `clawgauge.character-evidence.v1`:

```json
{
  "schemaVersion": "clawgauge.character-evidence.v1",
  "evidenceScope": "persona-naturalness",
  "scenario": {
    "id": "character-vibes-gollum",
    "definitionSha256": "64 lowercase hex characters"
  },
  "candidates": [
    {
      "model": "provider/model",
      "requestedProvider": "provider",
      "requestedModel": "model",
      "observedProvider": "provider",
      "observedModel": "model",
      "identityVerified": true,
      "identityProofSha256": "64 lowercase hex characters",
      "requestedThinking": "high",
      "observedThinking": "high",
      "reasoningVerified": true,
      "reasoningProofSha256": "64 lowercase hex characters",
      "requestedFastMode": false,
      "observedFastMode": false,
      "fallbackDisabled": true,
      "fallbackUsed": false,
      "fallbackProofSha256": "64 lowercase hex characters",
      "transcriptComplete": true,
      "transcriptSha256": "64 lowercase hex characters"
    }
  ],
  "judges": [
    {
      "requestedModel": "provider/judge",
      "observedModel": "provider/judge",
      "providerFamily": "provider",
      "providerFamilyVerified": true,
      "identityVerified": true,
      "identityProofSha256": "64 lowercase hex characters",
      "reasoningVerified": true,
      "reasoningProofSha256": "64 lowercase hex characters",
      "blindLabelsVerified": true,
      "blindLabelMapSha256": "64 lowercase hex characters"
    }
  ]
}
```

Rules:

1. `scenario.id` must equal the upstream summary's `scenarioId`.
2. `definitionSha256` hashes the exact pinned scenario definition used by the
   run. Record the OpenClaw commit in the surrounding campaign manifest.
3. `candidates` must exactly match the candidate model set. `requestedProvider`
   plus `requestedModel` must reconstruct the run route. The observed provider
   and model must exactly match that requested route; aliases, router rewrites,
   or otherwise misattributed observations block the result.
4. Candidate identity and reasoning must have retained proof hashes. Requested
   and observed thinking and fast-mode states must agree with the run's explicit
   `thinkingDefault` and boolean `fastMode`; missing run state blocks comparison.
5. Candidate fallback must be configured disabled, observed unused, and backed
   by a proof hash. A used, enabled, or unknown fallback blocks comparison.
6. Every candidate entry attests a complete transcript and its SHA-256. If the
   transcript remains embedded, the summarizer recomputes and verifies the hash.
   A scrubbed artifact may retain only the attested hash.
7. `judges` is ordered one-to-one with upstream `judgments`. Requested model,
   observed model, and provider family must come from trace/proxy evidence; do
   not infer a provider family from an arbitrary route-name prefix.
8. Identity, reasoning, fallback, and blind-label proofs are represented by SHA-256
   digests of the campaign's retained proof artifacts. Their corresponding
   `Verified` flags may be true only after those artifacts were checked.
9. Do not put tokens, prompts containing private data, absolute local paths, or
   raw trace credentials in the attestation.

The attestation records what was observed; it does not manufacture proof. If a
provider or router cannot expose observed identity, reasoning/fast state, or
fallback evidence, mark the layer unavailable instead of guessing.

## Ranking validity

Each accepted judge must:

- report that candidate labels were blind;
- have complete provenance under the contract above;
- rank every candidate exactly once;
- use integer, non-boolean ranks `1..n` without gaps; and
- retain the full candidate set used by every other judge.

Fractional ranks, booleans, missing candidates, duplicate candidates, and
unverified judge evidence invalidate that judge.

## Verdict states

- `usable`: every candidate passed with exact observed route, reasoning/fast
  state, disabled fallback, and transcript/scenario evidence; at least two valid
  judges span two explicitly verified provider families; and no provenance
  warning remains.
- `provisional`: core evidence verifies, but only one valid judge remains, judge
  families are not diverse, an extra invalid judgment exists, or a custom
  attested persona scenario was used. A provisional result has no route leader.
- `blocked`: any candidate failed; candidate route, thinking, fast mode, or
  fallback is missing/misattributed; scenario/candidate attestation is missing
  or inconsistent; or no fully ranked provenance-verified judge remains.

Split judges remain visible as `judge_agreement: split`; a tied mean rank remains
`leader: tie` only when the evidence is otherwise usable.

## Offline summarization

Embedded attestation:

```bash
python3 scripts/summarize_character_eval.py character-eval-summary.json \
  --out character-summary.md --json character-summary.json
```

Separate sidecar:

```bash
python3 scripts/summarize_character_eval.py character-eval-summary.json \
  --attestation character-evidence.json \
  --out character-summary.md --json character-summary.json
```

Generated summaries retain only input basenames and proof hashes, not absolute
filesystem paths.
