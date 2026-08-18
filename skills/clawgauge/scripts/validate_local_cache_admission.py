#!/usr/bin/env python3
"""Validate content-bound local-cache admission results against a frozen plan."""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any


PLAN_SCHEMA = "clawgauge.local-cache-admission-plan.v2"
RESULTS_SCHEMA = "clawgauge.local-cache-admission-results.v1"
SCORE_SCHEMA = "clawgauge.local-cache-admission-score.v1"
ARCHITECTURE_SCHEMA = "clawgauge.local-model-architecture.v1"
ROUTE_SCHEMA = "clawgauge.local-route-observation.v1"


def sha256_bytes(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def canonical_sha256(value: Any) -> str:
    raw = json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)
    return sha256_bytes(raw.encode())


def read_json(path: Path, blockers: list[str], label: str) -> tuple[dict[str, Any] | None, bytes | None]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        blockers.append(f"{label} is unreadable: {exc}")
        return None, None
    if not isinstance(value, dict):
        blockers.append(f"{label} is not a JSON object")
        return None, raw
    return value, raw


def safe_artifact(
    proof: Any,
    root: Path,
    blockers: list[str],
    label: str,
    *,
    expected_kind: str | None = None,
) -> tuple[dict[str, Any] | None, Path | None]:
    if not isinstance(proof, dict):
        blockers.append(f"{label} proof is missing")
        return None, None
    kind, reference, claimed = proof.get("kind"), proof.get("reference"), proof.get("sha256")
    if not isinstance(kind, str) or not kind.strip() or (expected_kind and kind != expected_kind):
        blockers.append(f"{label} proof kind is invalid")
    if not isinstance(reference, str) or not reference.strip():
        blockers.append(f"{label} proof reference is missing")
        return proof, None
    relative = Path(reference)
    if relative.is_absolute() or ".." in relative.parts:
        blockers.append(f"{label} proof reference must be a safe relative path")
        return proof, None
    path = (root / relative).resolve()
    resolved_root = root.resolve()
    if path != resolved_root and resolved_root not in path.parents:
        blockers.append(f"{label} proof reference escapes the artifact root")
        return proof, None
    try:
        raw = path.read_bytes()
    except OSError as exc:
        blockers.append(f"{label} proof artifact is unreadable: {exc}")
        return proof, None
    if claimed != sha256_bytes(raw):
        blockers.append(f"{label} proof artifact hash mismatch")
    return proof, path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("plan", type=Path)
    parser.add_argument("results", type=Path)
    parser.add_argument("--artifact-root", type=Path, required=True)
    parser.add_argument("--out", type=Path)
    args = parser.parse_args()

    blockers: list[str] = []
    plan, plan_raw = read_json(args.plan, blockers, "plan")
    results, results_raw = read_json(args.results, blockers, "results")
    root = args.artifact_root.resolve()
    if not root.is_dir():
        blockers.append("artifact root is not a directory")

    plan = plan or {}
    results = results or {}
    if plan.get("schema_version") != PLAN_SCHEMA:
        blockers.append("plan schema is invalid")
    if plan.get("ok_to_execute") is not True or plan.get("blockers") != []:
        blockers.append("plan is not executable")
    provenance = plan.get("provenance") if isinstance(plan.get("provenance"), dict) else {}
    fingerprint = canonical_sha256(provenance)
    if plan.get("plan_fingerprint") != fingerprint:
        blockers.append("plan fingerprint is invalid")
    if results.get("schema_version") != RESULTS_SCHEMA:
        blockers.append("results schema is invalid")
    if results.get("plan_fingerprint") != fingerprint:
        blockers.append("results plan fingerprint differs from the plan")
    if plan_raw is not None and results.get("plan_sha256") != sha256_bytes(plan_raw):
        blockers.append("results plan hash differs from the plan artifact")
    if results.get("provenance") != provenance:
        blockers.append("results provenance differs from the frozen plan")
    if results.get("blockers") != []:
        blockers.append("results contain blockers")

    expected_cases = [
        item.get("id") for item in plan.get("cases", []) if isinstance(item, dict)
    ]
    raw_cases = results.get("cases") if isinstance(results.get("cases"), list) else []
    case_ids = [item.get("id") for item in raw_cases if isinstance(item, dict)]
    if len(case_ids) != len(set(case_ids)):
        blockers.append("results contain duplicate case IDs")
    if set(case_ids) != set(expected_cases) or len(case_ids) != len(expected_cases):
        blockers.append("results cases do not exactly match the frozen plan")

    proof_count = 0
    for item in raw_cases:
        if not isinstance(item, dict):
            blockers.append("results contain a non-object case")
            continue
        case_id = str(item.get("id") or "missing")
        if item.get("status") != "pass":
            blockers.append(f"case {case_id} did not pass")
        evidence = item.get("evidence") if isinstance(item.get("evidence"), list) else []
        if not evidence:
            blockers.append(f"case {case_id} has no content-bound evidence")
        for index, proof in enumerate(evidence):
            safe_artifact(proof, root, blockers, f"case {case_id} evidence {index}")
            proof_count += 1

    architecture_proof, architecture_path = safe_artifact(
        results.get("architecture_manifest_proof"),
        root,
        blockers,
        "architecture manifest",
        expected_kind="clawgauge-local-architecture-manifest",
    )
    route_proof, route_path = safe_artifact(
        results.get("openclaw_route_proof"),
        root,
        blockers,
        "OpenClaw route observation",
        expected_kind="clawgauge-local-route-observation",
    )
    architecture, _ = read_json(architecture_path, blockers, "architecture manifest") if architecture_path else (None, None)
    route, _ = read_json(route_path, blockers, "OpenClaw route observation") if route_path else (None, None)
    architecture = architecture or {}
    route = route or {}

    if architecture.get("schema_version") != ARCHITECTURE_SCHEMA:
        blockers.append("architecture manifest schema is invalid")
    architecture_expected = {
        "model": provenance.get("model"),
        "loaded_model": provenance.get("loaded_model"),
        "model_revision": provenance.get("model_revision"),
        "architecture_fingerprint": provenance.get("architecture_fingerprint"),
        "features": provenance.get("features"),
    }
    if any(architecture.get(key) != value for key, value in architecture_expected.items()):
        blockers.append("architecture manifest differs from the frozen plan")

    if route.get("schema_version") != ROUTE_SCHEMA:
        blockers.append("OpenClaw route observation schema is invalid")
    route_expected = {
        key: provenance.get(key)
        for key in (
            "runtime", "runtime_version", "mlx_version", "provider", "model",
            "loaded_model", "model_revision", "openclaw_version", "openclaw_commit",
            "architecture_fingerprint", "template_fingerprint",
            "parser_fingerprint", "cache_policy_fingerprint", "cache_layout_fingerprint",
            "features",
        )
    }
    if any(route.get(key) != value for key, value in route_expected.items()):
        blockers.append("OpenClaw route observation differs from the frozen plan")
    explicit_route_expected = {
        "requested_provider": provenance.get("provider"),
        "requested_model": provenance.get("model"),
        "observed_provider": provenance.get("provider"),
        "observed_model": provenance.get("model"),
        "response_model": provenance.get("model"),
    }
    if any(route.get(key) != value for key, value in explicit_route_expected.items()):
        blockers.append(
            "OpenClaw requested/observed/response route differs from the frozen plan"
        )
    if route.get("fallback_used") is not False:
        blockers.append("OpenClaw route observation reports fallback or omits fallback=false")
    for key in ("backend_started_at", "runtime_id", "cache_epoch"):
        if not isinstance(route.get(key), str) or not route[key].strip():
            blockers.append(f"OpenClaw route observation lacks {key}")
    if not isinstance(route.get("backend_pid"), int) or isinstance(route.get("backend_pid"), bool) or route["backend_pid"] <= 0:
        blockers.append("OpenClaw route observation lacks a positive backend_pid")

    blockers = list(dict.fromkeys(blockers))
    passed = not blockers
    score = {
        "schema_version": SCORE_SCHEMA,
        "passed": passed,
        "claim_granted": "cache-qualified" if passed else None,
        "provenance": provenance,
        "plan_fingerprint": fingerprint,
        "plan_sha256": sha256_bytes(plan_raw) if plan_raw is not None else None,
        "results_sha256": sha256_bytes(results_raw) if results_raw is not None else None,
        "case_count": len(expected_cases),
        "evidence_proof_count": proof_count,
        "architecture_manifest_sha256": architecture_proof.get("sha256") if architecture_proof else None,
        "openclaw_route_sha256": route_proof.get("sha256") if route_proof else None,
        "blockers": blockers,
        "claim_not_granted": ["operator-qualified", "promoted"],
    }
    rendered = json.dumps(score, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    return 0 if passed else 2


if __name__ == "__main__":
    raise SystemExit(main())
