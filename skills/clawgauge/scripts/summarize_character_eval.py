#!/usr/bin/env python3
"""Summarize attested OpenClaw persona/naturalness character evidence."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import statistics
import sys
from collections import Counter
from pathlib import Path
from typing import Any


ATTESTATION_SCHEMA = "clawgauge.character-evidence.v1"
EVIDENCE_SCOPE = "persona-naturalness"
BUILTIN_PERSONA_SCENARIOS = {
    "character-vibes-c3po",
    "character-vibes-gollum",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
PROVIDER_FAMILY_RE = re.compile(r"^[a-z0-9][a-z0-9._-]*$")


def read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"{path.name}: JSON root must be an object")
    return data


def read_attestation(data: dict[str, Any], path: Path | None) -> dict[str, Any] | None:
    container = read_json(path) if path else data
    value = container.get("clawgaugeAttestation", container if path else None)
    if value is None:
        return None
    if not isinstance(value, dict):
        raise ValueError("ClawGauge character attestation must be a JSON object")
    return value


def sha256_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def is_sha256(value: Any) -> bool:
    return isinstance(value, str) and SHA256_RE.fullmatch(value.lower()) is not None


def is_nonempty_string(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def complete_rankings(rankings: list[dict[str, Any]], model_set: set[str]) -> bool:
    ranked_models = [str(item.get("model")) for item in rankings if item.get("model")]
    ranks = [item.get("rank") for item in rankings]
    return (
        bool(model_set)
        and len(rankings) == len(model_set)
        and len(set(ranked_models)) == len(model_set)
        and set(ranked_models) == model_set
        and all(type(rank) is int for rank in ranks)
        and sorted(ranks) == list(range(1, len(model_set) + 1))
    )


def validate_attestation_root(
    attestation: dict[str, Any] | None,
    scenario_id: str,
) -> tuple[list[str], str | None]:
    blockers: list[str] = []
    fingerprint: str | None = None
    if attestation is None:
        return ["missing versioned ClawGauge character-evidence attestation"], None
    if attestation.get("schemaVersion") != ATTESTATION_SCHEMA:
        blockers.append(f"attestation schema must be {ATTESTATION_SCHEMA}")
    if attestation.get("evidenceScope") != EVIDENCE_SCOPE:
        blockers.append("attestation evidenceScope must be persona-naturalness")
    scenario = attestation.get("scenario")
    if not isinstance(scenario, dict):
        blockers.append("attestation scenario record is missing")
    else:
        if scenario.get("id") != scenario_id:
            blockers.append("attested scenario id does not match the summary")
        value = scenario.get("definitionSha256")
        if not is_sha256(value):
            blockers.append("scenario definitionSha256 is missing or invalid")
        else:
            fingerprint = str(value).lower()
    return blockers, fingerprint


def validate_candidate_evidence(
    attestation: dict[str, Any] | None,
    runs: list[dict[str, Any]],
    models: list[str],
) -> tuple[list[str], list[dict[str, Any]]]:
    blockers: list[str] = []
    output: list[dict[str, Any]] = []
    records = attestation.get("candidates") if attestation else None
    if not isinstance(records, list):
        return ["attestation candidates must be a complete list"], output
    typed = [item for item in records if isinstance(item, dict)]
    by_model: dict[str, dict[str, Any]] = {}
    duplicate_records: list[str] = []
    for item in typed:
        model = str(item.get("model") or "")
        if model in by_model:
            duplicate_records.append(model or "unknown")
        by_model[model] = item
    if len(typed) != len(records):
        blockers.append("attestation contains a non-object candidate record")
    if duplicate_records:
        blockers.append(f"duplicate candidate attestation records: {sorted(set(duplicate_records))}")
    if set(by_model) != set(models):
        blockers.append("attested candidate set does not exactly match the run candidate set")

    run_by_model = {str(item.get("model")): item for item in runs}
    for model in models:
        record = by_model.get(model)
        if record is None:
            continue
        run = run_by_model.get(model, {})
        errors: list[str] = []
        digest = record.get("transcriptSha256")
        if record.get("transcriptComplete") is not True:
            errors.append("transcriptComplete is not attested true")
        if not is_sha256(digest):
            errors.append("transcriptSha256 is missing or invalid")
        transcript = run.get("transcript")
        transcript_present = isinstance(transcript, str) and bool(transcript)
        if transcript_present and is_sha256(digest):
            if sha256_text(transcript) != str(digest).lower():
                errors.append("transcript hash does not match the embedded transcript")

        requested_provider = record.get("requestedProvider")
        requested_model = record.get("requestedModel")
        observed_provider = record.get("observedProvider")
        observed_model = record.get("observedModel")
        route_parts = (
            requested_provider,
            requested_model,
            observed_provider,
            observed_model,
        )
        if not all(is_nonempty_string(value) for value in route_parts):
            errors.append("requested/observed provider and model are required")
        else:
            requested_route = f"{str(requested_provider).strip()}/{str(requested_model).strip()}"
            observed_route = f"{str(observed_provider).strip()}/{str(observed_model).strip()}"
            if requested_route != model:
                errors.append("requested provider/model does not match the run route")
            if observed_route != requested_route:
                errors.append("observed provider/model is misattributed from the requested route")
        if record.get("identityVerified") is not True or not is_sha256(
            record.get("identityProofSha256")
        ):
            errors.append("candidate identity proof is missing or unverified")

        requested_thinking = record.get("requestedThinking")
        observed_thinking = record.get("observedThinking")
        run_thinking = run.get("thinkingDefault")
        if not all(
            is_nonempty_string(value)
            for value in (requested_thinking, observed_thinking, run_thinking)
        ):
            errors.append("requested, observed, and run thinking states are required")
        elif not (requested_thinking == observed_thinking == run_thinking):
            errors.append("requested/observed thinking does not match run thinkingDefault")
        if record.get("reasoningVerified") is not True or not is_sha256(
            record.get("reasoningProofSha256")
        ):
            errors.append("candidate reasoning proof is missing or unverified")

        requested_fast = record.get("requestedFastMode")
        observed_fast = record.get("observedFastMode")
        run_fast = run.get("fastMode")
        if not all(type(value) is bool for value in (requested_fast, observed_fast, run_fast)):
            errors.append("requested, observed, and run fast states must be explicit booleans")
        elif not (requested_fast == observed_fast == run_fast):
            errors.append("requested/observed fast state does not match run fastMode")

        if record.get("fallbackDisabled") is not True:
            errors.append("candidate fallback is not attested disabled")
        if record.get("fallbackUsed") is not False:
            errors.append("candidate fallback was used or its state is unknown")
        if not is_sha256(record.get("fallbackProofSha256")):
            errors.append("candidate fallback proof is missing or invalid")
        if errors:
            blockers.append(f"candidate {model}: {'; '.join(errors)}")
        output.append(
            {
                "model": model,
                "requested_route": (
                    f"{requested_provider}/{requested_model}"
                    if is_nonempty_string(requested_provider)
                    and is_nonempty_string(requested_model)
                    else None
                ),
                "observed_route": (
                    f"{observed_provider}/{observed_model}"
                    if is_nonempty_string(observed_provider)
                    and is_nonempty_string(observed_model)
                    else None
                ),
                "thinking": run_thinking,
                "fast_mode": run_fast if type(run_fast) is bool else None,
                "fallback_disabled": record.get("fallbackDisabled") is True,
                "fallback_used": record.get("fallbackUsed"),
                "mode": "embedded-and-hashed" if transcript_present else "attested-hash-only",
                "transcript_sha256": str(digest).lower() if is_sha256(digest) else None,
                "verified": not errors,
            }
        )
    return blockers, output


def validate_judge(
    judgment: dict[str, Any],
    evidence: dict[str, Any] | None,
    model_set: set[str],
) -> tuple[list[str], list[dict[str, Any]]]:
    errors: list[str] = []
    rankings = [item for item in judgment.get("rankings", []) if isinstance(item, dict)]
    if not complete_rankings(rankings, model_set):
        errors.append("rankings must cover every candidate exactly once with integral consecutive ranks")
    if judgment.get("blindModels") is not True:
        errors.append("upstream judgment does not report blind candidate labels")
    if evidence is None:
        errors.append("missing ordered judge attestation")
        return errors, rankings

    requested = evidence.get("requestedModel")
    observed = evidence.get("observedModel")
    family = evidence.get("providerFamily")
    if requested != judgment.get("model") or not is_nonempty_string(requested):
        errors.append("requested judge identity does not match the judgment route")
    if not is_nonempty_string(observed):
        errors.append("observed judge identity is missing")
    if not is_nonempty_string(family) or PROVIDER_FAMILY_RE.fullmatch(str(family)) is None:
        errors.append("verified provider family is missing or invalid")
    if evidence.get("providerFamilyVerified") is not True:
        errors.append("provider family is not attested verified")
    if evidence.get("identityVerified") is not True or not is_sha256(
        evidence.get("identityProofSha256")
    ):
        errors.append("judge identity proof is missing or unverified")
    if evidence.get("reasoningVerified") is not True or not is_sha256(
        evidence.get("reasoningProofSha256")
    ):
        errors.append("judge reasoning proof is missing or unverified")
    if evidence.get("blindLabelsVerified") is not True or not is_sha256(
        evidence.get("blindLabelMapSha256")
    ):
        errors.append("blind-label proof is missing or unverified")
    return errors, rankings


def build_summary(
    data: dict[str, Any],
    source: Path,
    attestation: dict[str, Any] | None,
    attestation_source: Path | None,
) -> dict[str, Any]:
    runs = [item for item in data.get("runs", []) if isinstance(item, dict)]
    judgments = [item for item in data.get("judgments", []) if isinstance(item, dict)]
    raw_models = [str(item.get("model")) for item in runs if item.get("model")]
    models = list(dict.fromkeys(raw_models))
    model_set = set(models)
    scenario_id = str(data.get("scenarioId") or "")
    blockers, scenario_fingerprint = validate_attestation_root(attestation, scenario_id)
    warnings: list[str] = []

    if not scenario_id:
        blockers.append("summary scenarioId is missing")
    elif scenario_id not in BUILTIN_PERSONA_SCENARIOS:
        warnings.append("custom scenario: evidence remains limited to its attested persona/naturalness scope")
    if not models:
        blockers.append("no candidate runs were present")
    if len(raw_models) != len(models):
        blockers.append("duplicate candidate routes were present")
    failed_candidates = [
        str(item.get("model") or "unknown")
        for item in runs
        if str(item.get("status") or "").lower() != "pass"
    ]
    if failed_candidates:
        blockers.append(f"candidate run failures: {failed_candidates}")

    candidate_errors, transcript_evidence = validate_candidate_evidence(attestation, runs, models)
    blockers.extend(candidate_errors)

    attested_judges = attestation.get("judges") if attestation else None
    if not isinstance(attested_judges, list):
        attested_judges = []
        if attestation is not None:
            blockers.append("attestation judges must be an ordered list")
    valid_judges: list[dict[str, Any]] = []
    invalid_judges: list[dict[str, Any]] = []
    for index, judgment in enumerate(judgments):
        evidence = attested_judges[index] if index < len(attested_judges) else None
        if not isinstance(evidence, dict):
            evidence = None
        errors, rankings = validate_judge(judgment, evidence, model_set)
        if errors:
            invalid_judges.append(
                {
                    "requested_model": judgment.get("model"),
                    "errors": errors,
                }
            )
            continue
        valid_judges.append(
            {
                "judgment": judgment,
                "rankings": rankings,
                "requested_model": evidence.get("requestedModel"),
                "observed_model": evidence.get("observedModel"),
                "provider_family": evidence.get("providerFamily"),
                "identity_proof_sha256": str(evidence.get("identityProofSha256")).lower(),
                "reasoning_proof_sha256": str(evidence.get("reasoningProofSha256")).lower(),
            }
        )
    if len(attested_judges) > len(judgments):
        warnings.append("attestation includes judge records with no matching judgment")
    if invalid_judges:
        warnings.append(f"{len(invalid_judges)} judge result(s) lacked complete rankings or provenance")
    if not valid_judges:
        blockers.append("no fully ranked, provenance-verified judge result was available")

    aggregates: dict[str, dict[str, Any]] = {
        model: {
            "ranks": [],
            "scores": [],
            "wins": 0,
            "strengths": [],
            "weaknesses": [],
            "summaries": [],
        }
        for model in models
    }
    top_choices: list[str] = []
    for valid in valid_judges:
        rankings = sorted(valid["rankings"], key=lambda item: item["rank"])
        if rankings:
            top_choices.append(str(rankings[0].get("model")))
        for ranking in rankings:
            model = str(ranking.get("model"))
            if model not in aggregates:
                continue
            rank = ranking.get("rank")
            score = ranking.get("score")
            if type(rank) is int:
                aggregates[model]["ranks"].append(float(rank))
                if rank == 1:
                    aggregates[model]["wins"] += 1
            if is_number(score):
                aggregates[model]["scores"].append(float(score))
            aggregates[model]["strengths"].extend(
                str(item) for item in ranking.get("strengths", []) if str(item).strip()
            )
            aggregates[model]["weaknesses"].extend(
                str(item) for item in ranking.get("weaknesses", []) if str(item).strip()
            )
            if str(ranking.get("summary") or "").strip():
                aggregates[model]["summaries"].append(str(ranking["summary"]).strip())

    rows: list[dict[str, Any]] = []
    run_by_model = {str(item.get("model")): item for item in runs}
    for model in models:
        item = aggregates[model]
        ranks = item["ranks"]
        scores = item["scores"]
        run = run_by_model.get(model, {})
        rows.append(
            {
                "model": model,
                "status": run.get("status"),
                "thinking": run.get("thinkingDefault"),
                "fast_mode": run.get("fastMode"),
                "duration_ms": run.get("durationMs"),
                "mean_rank": statistics.mean(ranks) if ranks else None,
                "rank_stdev": statistics.pstdev(ranks) if len(ranks) > 1 else (0.0 if ranks else None),
                "rank_range": [min(ranks), max(ranks)] if ranks else None,
                "mean_score": statistics.mean(scores) if scores else None,
                "wins": item["wins"],
                "judge_count": len(ranks),
                "strengths": list(dict.fromkeys(item["strengths"])),
                "weaknesses": list(dict.fromkeys(item["weaknesses"])),
                "judge_summaries": item["summaries"],
                "error": run.get("error"),
            }
        )

    families = sorted({str(item["provider_family"]) for item in valid_judges})
    all_blind = bool(valid_judges) and all(
        item["judgment"].get("blindModels") is True for item in valid_judges
    )
    if len(valid_judges) < 2:
        warnings.append("fewer than two valid judges")
    if len(families) < 2:
        warnings.append("verified judges do not span two provider families")
    requested_models = [str(item["requested_model"]) for item in valid_judges]
    observed_models = [str(item["observed_model"]) for item in valid_judges]
    if len(set(requested_models)) != len(requested_models):
        warnings.append("duplicate requested judge routes were used")
    if len(set(observed_models)) != len(observed_models):
        warnings.append("duplicate observed judge routes were used")
    overlap = sorted(model_set & set(observed_models))
    if overlap:
        warnings.append(f"observed judge routes overlap candidate routes: {overlap}")

    if blockers:
        status = "blocked"
    elif warnings:
        status = "provisional"
    else:
        status = "usable"

    top_counts = Counter(top_choices)
    if not top_counts:
        agreement = "unavailable"
    elif len(top_counts) == 1:
        agreement = "unanimous"
    elif top_counts.most_common(1)[0][1] > len(top_choices) / 2:
        agreement = "majority"
    else:
        agreement = "split"

    leader = "indeterminate"
    ranked_rows = [row for row in rows if row["mean_rank"] is not None]
    if status == "usable" and ranked_rows:
        best = min(float(row["mean_rank"]) for row in ranked_rows)
        winners = [row["model"] for row in ranked_rows if float(row["mean_rank"]) == best]
        leader = winners[0] if len(winners) == 1 else "tie"

    return {
        "schema_version": 2,
        "source_file": source.name,
        "attestation_source_file": attestation_source.name if attestation_source else source.name,
        "attestation_schema": attestation.get("schemaVersion") if attestation else None,
        "evidence_scope": EVIDENCE_SCOPE,
        "scenario_id": scenario_id or None,
        "scenario_definition_sha256": scenario_fingerprint,
        "evidence_status": status,
        "leader": leader,
        "judge_agreement": agreement,
        "top_choice_counts": dict(top_counts),
        "valid_judges": len(valid_judges),
        "invalid_judges": invalid_judges,
        "judge_provider_families": families,
        "judge_provenance": [
            {
                key: value
                for key, value in item.items()
                if key not in {"judgment", "rankings"}
            }
            for item in valid_judges
        ],
        "all_valid_judges_blind": all_blind,
        "candidate_transcript_evidence": transcript_evidence,
        "failed_candidates": failed_candidates,
        "blockers": blockers,
        "warnings": warnings,
        "models": rows,
    }


def fmt(value: Any, digits: int = 2) -> str:
    return "n/a" if not is_number(value) else f"{float(value):.{digits}f}"


def render(summary: dict[str, Any]) -> str:
    lines = [
        "# ClawGauge — Persona and Naturalness Summary",
        "",
        f"- Scenario: `{summary['scenario_id'] or 'n/a'}`",
        f"- Evidence scope: **{summary['evidence_scope']}**",
        f"- Evidence: **{summary['evidence_status']}**",
        f"- Leader: **{summary['leader']}**",
        f"- Judge agreement: **{summary['judge_agreement']}**",
        f"- Valid judges / verified provider families: "
        f"{summary['valid_judges']} / {len(summary['judge_provider_families'])}",
        f"- Blind labels: {summary['all_valid_judges_blind']}",
        "- This layer measures persona commitment and conversational naturalness. It is not evidence of general intent inference.",
        "- Judge rankings are subjective evidence; deterministic QA and task completion remain higher priority.",
        "",
    ]
    if summary["blockers"]:
        lines.extend(["## Blockers", ""])
        lines.extend(f"- {item}" for item in summary["blockers"])
        lines.append("")
    if summary["warnings"]:
        lines.extend(["## Limitations", ""])
        lines.extend(f"- {item}" for item in summary["warnings"])
        lines.append("")

    lines.extend(
        [
            "## Candidate Read",
            "",
            "| Model | Run | Thinking | Fast | Mean rank | Rank spread | Mean score | Wins |",
            "|---|---|---|---|---:|---:|---:|---:|",
        ]
    )
    for row in summary["models"]:
        lines.append(
            f"| `{row['model']}` | {row['status'] or 'n/a'} | "
            f"{row['thinking'] or 'n/a'} | {row['fast_mode']!r} | "
            f"{fmt(row['mean_rank'])} | {fmt(row['rank_stdev'])} | "
            f"{fmt(row['mean_score'], 1)} | {row['wins']} |"
        )
    lines.append("")

    for row in summary["models"]:
        lines.extend([f"### {row['model']}", ""])
        strengths = row["strengths"][:5]
        weaknesses = row["weaknesses"][:5]
        lines.append("- Strengths: " + ("; ".join(strengths) if strengths else "n/a"))
        lines.append("- Weaknesses: " + ("; ".join(weaknesses) if weaknesses else "n/a"))
        if row["error"]:
            lines.append(f"- Run error: {row['error']}")
        lines.append("")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", type=Path)
    parser.add_argument(
        "--attestation",
        type=Path,
        help="Optional sidecar containing clawgauge.character-evidence.v1",
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument("--json", dest="json_out", type=Path)
    args = parser.parse_args()
    try:
        data = read_json(args.summary)
        attestation = read_attestation(data, args.attestation)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    summary = build_summary(data, args.summary, attestation, args.attestation)
    report = render(summary) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(report, encoding="utf-8")
    else:
        sys.stdout.write(report)
    if args.json_out:
        args.json_out.parent.mkdir(parents=True, exist_ok=True)
        args.json_out.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    return 0 if summary["evidence_status"] != "blocked" else 2


if __name__ == "__main__":
    raise SystemExit(main())
