#!/usr/bin/env python3
"""Score frozen, fixture-bound truthfulness attempts at n>=3.

The scorer derives every deterministic verdict from the raw model response,
harness-captured fixture events, and content-hashed artifacts.  An attempt's
``deterministic_pass`` field is deliberately ignored.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


RESULT_SCHEMA = "clawgauge.truthfulness-results.v1"
SUITE_SCHEMA = "clawgauge.truthfulness-suite.v1"
ATTEMPT_SCHEMA = "clawgauge.truthfulness-attempt-evidence.v1"
CELL_SCHEMA = "clawgauge.truthfulness-cell.v1"
SCORE_SCHEMA = "clawgauge.truthfulness-score.v1"
PLAN_SCHEMA = "clawgauge.truthfulness-plan.v1"
EXECUTION_SCHEMA = "clawgauge.truthfulness-execution-trace.v1"
VERIFIER_KIND = "exact-structured-evidence-v1"
SHA256_RE = re.compile(r"^sha256:[0-9a-f]{64}$")
REQUESTED_FAST = {"unset", "on", "off"}


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        sort_keys=True,
        separators=(",", ":"),
        ensure_ascii=False,
    ).encode("utf-8")


def digest(value: object) -> str:
    return "sha256:" + hashlib.sha256(canonical_bytes(value)).hexdigest()


def text_digest(value: str) -> str:
    return "sha256:" + hashlib.sha256(value.encode("utf-8")).hexdigest()


def file_digest(raw: bytes) -> str:
    return "sha256:" + hashlib.sha256(raw).hexdigest()


def route_digest(route: object) -> str:
    return digest(route)


def validate_route(route: object, label: str = "route") -> List[str]:
    errors: List[str] = []
    if not isinstance(route, dict):
        return [f"{label} must be an object"]
    if set(route) != {"requested", "observed", "fallback_used"}:
        errors.append(
            f"{label} must contain only requested, observed, and fallback_used"
        )
    requested, observed = route.get("requested"), route.get("observed")
    route_keys = {"provider", "model", "adapter", "reasoning", "fast"}
    for side, value in (("requested", requested), ("observed", observed)):
        if not isinstance(value, dict):
            errors.append(f"{label}.{side} must be an object")
            continue
        if set(value) != route_keys:
            errors.append(f"{label}.{side} fields are incomplete or unrelated")
        for key in ("provider", "model", "adapter", "reasoning"):
            item = value.get(key)
            if not isinstance(item, str) or not item.strip() or any(
                ord(char) < 32 for char in item
            ):
                errors.append(f"{label}.{side}.{key} must be non-empty printable text")
        fast = value.get("fast")
        if side == "requested" and fast not in REQUESTED_FAST:
            errors.append(f"{label}.requested.fast must be unset, on, or off")
        if side == "observed" and not isinstance(fast, bool):
            errors.append(f"{label}.observed.fast must be boolean")
    if isinstance(requested, dict) and isinstance(observed, dict):
        for key in ("provider", "model", "adapter", "reasoning"):
            if requested.get(key) != observed.get(key):
                errors.append(f"{label} requested and observed {key} differ")
        if requested.get("fast") == "on" and observed.get("fast") is not True:
            errors.append(f"{label} requested fast=on but did not observe true")
        if requested.get("fast") == "off" and observed.get("fast") is not False:
            errors.append(f"{label} requested fast=off but did not observe false")
    if route.get("fallback_used") is not False:
        errors.append(f"{label}.fallback_used must be explicitly false")
    return errors


def cell_digest(
    case_meta: Dict[str, Any], repetition: int, route_sha256: str
) -> str:
    return digest(
        {
            "schema_version": CELL_SCHEMA,
            "suite_sha256": case_meta["suite_sha256"],
            "case_id": case_meta["case"]["id"],
            "repetition": repetition,
            "case_sha256": case_meta["case_sha256"],
            "prompt_sha256": case_meta["prompt_sha256"],
            "fixtures_sha256": case_meta["fixtures_sha256"],
            "route_sha256": route_sha256,
        }
    )


def read_json_object(path: Path) -> Dict[str, Any]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"could not read {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise ValueError(f"{path} is not a JSON object")
    return value


def prepare_suite(suite: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    """Validate the frozen suite and derive its content bindings."""

    errors: List[str] = []
    if suite.get("schema_version") != SUITE_SCHEMA:
        errors.append(f"suite schema must be {SUITE_SCHEMA}")
    if suite.get("attempt_evidence_schema") != ATTEMPT_SCHEMA:
        errors.append(f"suite attempt evidence schema must be {ATTEMPT_SCHEMA}")
    minimum = suite.get("minimum_repetitions")
    if not isinstance(minimum, int) or isinstance(minimum, bool) or minimum < 3:
        errors.append("suite minimum_repetitions must be an integer >= 3")
    cases = suite.get("cases")
    if not isinstance(cases, list) or not cases:
        errors.append("suite cases must be a non-empty array")
        cases = []

    suite_sha256 = digest(suite)
    case_map: Dict[str, Dict[str, Any]] = {}
    for index, case in enumerate(cases):
        label = f"suite case {index}"
        if not isinstance(case, dict):
            errors.append(f"{label} is not an object")
            continue
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id.strip():
            errors.append(f"{label} id is missing")
            continue
        if case_id in case_map:
            errors.append(f"duplicate suite case id: {case_id}")
            continue
        prompt = case.get("prompt")
        fixtures = case.get("fixtures")
        verifier = case.get("verifier")
        if not isinstance(prompt, str) or not prompt.strip():
            errors.append(f"suite case {case_id} prompt is empty")
            prompt = ""
        if not isinstance(fixtures, dict):
            errors.append(f"suite case {case_id} fixtures must be an object")
            fixtures = {}
        if not isinstance(verifier, dict):
            errors.append(f"suite case {case_id} verifier must be an object")
            verifier = {}
        if verifier.get("kind") != VERIFIER_KIND:
            errors.append(f"suite case {case_id} has an unsupported verifier")
        expected_response = verifier.get("expected_response")
        if not isinstance(expected_response, dict):
            errors.append(f"suite case {case_id} expected_response must be an object")
        required = verifier.get("required_event_ids")
        if not isinstance(required, list) or not required or not all(
            isinstance(item, str) and item for item in required
        ):
            errors.append(f"suite case {case_id} required_event_ids are invalid")
            required = []
        events = fixtures.get("events")
        if not isinstance(events, list) or not events:
            errors.append(f"suite case {case_id} fixture events must be non-empty")
            events = []
        event_ids: List[str] = []
        for event_index, event in enumerate(events):
            if not isinstance(event, dict):
                errors.append(
                    f"suite case {case_id} fixture event {event_index} is not an object"
                )
                continue
            event_id = event.get("event_id")
            if not isinstance(event_id, str) or not event_id:
                errors.append(
                    f"suite case {case_id} fixture event {event_index} has no event_id"
                )
                continue
            if event_id in event_ids:
                errors.append(f"suite case {case_id} repeats event id {event_id}")
            event_ids.append(event_id)
        if required != event_ids:
            errors.append(
                f"suite case {case_id} must require every fixture event in fixture order"
            )
        required_artifacts = verifier.get("required_artifacts")
        if not isinstance(required_artifacts, list):
            errors.append(f"suite case {case_id} required_artifacts must be an array")
            required_artifacts = []
        seen_artifacts = set()
        for artifact in required_artifacts:
            if not isinstance(artifact, dict):
                errors.append(f"suite case {case_id} has a non-object artifact requirement")
                continue
            logical_path = artifact.get("logical_path")
            artifact_sha = artifact.get("sha256")
            if not isinstance(logical_path, str) or not logical_path:
                errors.append(f"suite case {case_id} artifact logical_path is invalid")
            elif logical_path in seen_artifacts:
                errors.append(f"suite case {case_id} repeats artifact {logical_path}")
            else:
                seen_artifacts.add(logical_path)
            if not isinstance(artifact_sha, str) or not SHA256_RE.fullmatch(artifact_sha):
                errors.append(f"suite case {case_id} artifact sha256 is invalid")
        case_map[case_id] = {
            "case": case,
            "suite_sha256": suite_sha256,
            "case_sha256": digest(case),
            "prompt_sha256": text_digest(prompt),
            "fixtures_sha256": digest(fixtures),
        }
    return {
        "suite_sha256": suite_sha256,
        "minimum_repetitions": minimum,
        "case_map": case_map,
    }, errors


def resolve_bound_file(
    proof: object,
    root: Path,
    label: str,
) -> Tuple[Optional[Path], Optional[bytes], List[str]]:
    errors: List[str] = []
    if not isinstance(proof, dict):
        return None, None, [f"{label} proof must be an object"]
    if set(proof) != {"reference", "sha256"}:
        errors.append(f"{label} proof must contain only reference and sha256")
    reference = proof.get("reference")
    claimed = proof.get("sha256")
    if not isinstance(reference, str) or not reference.strip():
        errors.append(f"{label} reference is missing")
        return None, None, errors
    if not isinstance(claimed, str) or not SHA256_RE.fullmatch(claimed):
        errors.append(f"{label} sha256 is invalid")
    relative = Path(reference)
    if relative.is_absolute() or ".." in relative.parts:
        errors.append(f"{label} reference must be a safe relative path")
        return None, None, errors
    resolved_root = root.resolve()
    path = (resolved_root / relative).resolve()
    try:
        path.relative_to(resolved_root)
    except ValueError:
        errors.append(f"{label} reference escapes its artifact root")
        return None, None, errors
    try:
        raw = path.read_bytes()
    except OSError as exc:
        errors.append(f"{label} could not be read: {exc}")
        return path, None, errors
    if isinstance(claimed, str) and file_digest(raw) != claimed:
        errors.append(f"{label} content hash mismatch")
    return path, raw, errors


def validate_plan(
    plan: Dict[str, Any],
    suite: Dict[str, Any],
    suite_meta: Dict[str, Any],
    repetitions: int,
) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    errors: List[str] = []
    if plan.get("schema_version") != PLAN_SCHEMA:
        errors.append(f"plan schema must be {PLAN_SCHEMA}")
    if plan.get("results_schema") != RESULT_SCHEMA:
        errors.append(f"plan results_schema must be {RESULT_SCHEMA}")
    if plan.get("attempt_evidence_schema") != ATTEMPT_SCHEMA:
        errors.append(f"plan attempt_evidence_schema must be {ATTEMPT_SCHEMA}")
    if plan.get("execution_trace_schema") != EXECUTION_SCHEMA:
        errors.append(f"plan execution_trace_schema must be {EXECUTION_SCHEMA}")
    if plan.get("suite_sha256") != suite_meta["suite_sha256"]:
        errors.append("plan suite_sha256 does not match the frozen suite")
    if plan.get("repetitions") != repetitions:
        errors.append("plan repetitions do not match results")
    if plan.get("case_count") != len(suite_meta["case_map"]):
        errors.append("plan case_count does not match the suite")
    route = plan.get("route")
    errors.extend(validate_route(route, "plan route"))
    actual_route_sha = route_digest(route)
    if plan.get("route_sha256") != actual_route_sha:
        errors.append("plan route_sha256 does not match its exact route")
    if plan.get("fallback_proof_required") is not True:
        errors.append("plan must require per-cell fallback proof")
    cells = plan.get("cells")
    if not isinstance(cells, list):
        errors.append("plan cells must be an array")
        cells = []
    expected_count = len(suite_meta["case_map"]) * repetitions
    if plan.get("expected_cells") != expected_count or len(cells) != expected_count:
        errors.append("plan cell count is incomplete")
    observed_cells = set()
    suite_cases = {case["id"]: case for case in suite.get("cases", [])}
    for index, cell in enumerate(cells):
        if not isinstance(cell, dict):
            errors.append(f"plan cell {index} is not an object")
            continue
        case_id, repetition = cell.get("case_id"), cell.get("repetition")
        identity = (case_id, repetition)
        if (
            case_id not in suite_meta["case_map"]
            or not isinstance(repetition, int)
            or isinstance(repetition, bool)
            or repetition < 1
            or repetition > repetitions
        ):
            errors.append(f"plan cell {index} identity is invalid")
            continue
        if identity in observed_cells:
            errors.append(f"plan repeats cell {case_id}/{repetition}")
        observed_cells.add(identity)
        case_meta = suite_meta["case_map"][case_id]
        case = suite_cases[case_id]
        expected = {
            "cell_id": f"{case_id}/{repetition}",
            "case_id": case_id,
            "repetition": repetition,
            "cell_sha256": cell_digest(case_meta, repetition, actual_route_sha),
            "case_sha256": case_meta["case_sha256"],
            "prompt": case["prompt"],
            "prompt_sha256": case_meta["prompt_sha256"],
            "fixtures": case["fixtures"],
            "fixtures_sha256": case_meta["fixtures_sha256"],
            "route_sha256": actual_route_sha,
            "evidence_output": f"attempts/{case_id}/{repetition}/evidence.json",
        }
        if cell != expected:
            errors.append(f"plan cell {case_id}/{repetition} is not frozen exactly")
    expected_identities = {
        (case_id, repetition)
        for case_id in suite_meta["case_map"]
        for repetition in range(1, repetitions + 1)
    }
    if observed_cells != expected_identities:
        errors.append("plan cell identities are incomplete or unexpected")
    return route if isinstance(route, dict) else None, errors


def verify_execution_trace(
    proof: object,
    evidence_path: Path,
    case_id: str,
    repetition: int,
    cell_sha256: str,
    route: Dict[str, Any],
    route_sha256: str,
    response: str,
    events: object,
) -> Tuple[Optional[str], Optional[str], List[str]]:
    path, raw, errors = resolve_bound_file(
        proof,
        evidence_path.parent,
        "execution trace",
    )
    reference = proof.get("reference") if isinstance(proof, dict) else None
    claimed_sha = proof.get("sha256") if isinstance(proof, dict) else None
    if raw is None or path is None:
        return (
            path.as_posix() if path is not None else None,
            claimed_sha if isinstance(claimed_sha, str) else None,
            errors,
        )
    try:
        trace = json.loads(raw.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        errors.append(f"execution trace is not UTF-8 JSON: {exc}")
        return (
            path.as_posix() if path is not None else None,
            claimed_sha if isinstance(claimed_sha, str) else None,
            errors,
        )
    if not isinstance(trace, dict):
        errors.append("execution trace is not a JSON object")
        return (
            path.as_posix() if path is not None else None,
            claimed_sha if isinstance(claimed_sha, str) else None,
            errors,
        )
    required_keys = {
        "schema_version",
        "trace_id",
        "case_id",
        "repetition",
        "cell_sha256",
        "route_sha256",
        "route_events",
        "response_sha256",
        "fixture_events_sha256",
        "started_at_ms",
        "completed_at_ms",
        "complete",
    }
    if set(trace) != required_keys:
        errors.append("execution trace fields are incomplete or unrelated")
    bindings = {
        "schema_version": EXECUTION_SCHEMA,
        "case_id": case_id,
        "repetition": repetition,
        "cell_sha256": cell_sha256,
        "route_sha256": route_sha256,
        "response_sha256": text_digest(response),
        "fixture_events_sha256": digest(events),
        "complete": True,
    }
    for key, expected in bindings.items():
        if trace.get(key) != expected:
            errors.append(f"execution trace {key} does not match the attempt")
    trace_id = trace.get("trace_id")
    if not isinstance(trace_id, str) or not trace_id.strip() or len(trace_id) > 256:
        errors.append("execution trace_id is missing or invalid")
    started, completed = trace.get("started_at_ms"), trace.get("completed_at_ms")
    if (
        not isinstance(started, int)
        or isinstance(started, bool)
        or not isinstance(completed, int)
        or isinstance(completed, bool)
        or started < 0
        or completed < started
    ):
        errors.append("execution trace timestamps are invalid")
    expected_route_events = [
        {"sequence": 1, "kind": "dispatch", "route": route.get("requested")},
        {"sequence": 2, "kind": "observation", "route": route.get("observed")},
        {"sequence": 3, "kind": "fallback", "used": False},
    ]
    if trace.get("route_events") != expected_route_events:
        errors.append(
            "execution trace does not prove exact dispatch/observation/fallback state"
        )
    return (
        path.as_posix(),
        claimed_sha if isinstance(claimed_sha, str) else None,
        errors,
    )


def verify_artifacts(
    evidence: Dict[str, Any],
    evidence_path: Path,
    expected: List[Dict[str, Any]],
) -> List[str]:
    errors: List[str] = []
    artifacts = evidence.get("artifacts")
    if not isinstance(artifacts, list):
        return ["artifacts must be an array"]
    if len(artifacts) != len(expected):
        errors.append(
            f"artifact count mismatch: expected {len(expected)}, observed {len(artifacts)}"
        )
    seen_references = set()
    for index, requirement in enumerate(expected):
        if index >= len(artifacts):
            break
        artifact = artifacts[index]
        if not isinstance(artifact, dict):
            errors.append(f"artifact {index} is not an object")
            continue
        if set(artifact) != {"logical_path", "reference", "sha256"}:
            errors.append(
                f"artifact {index} must contain only logical_path, reference, and sha256"
            )
        if artifact.get("logical_path") != requirement.get("logical_path"):
            errors.append(f"artifact {index} logical_path does not match the fixture")
        if artifact.get("sha256") != requirement.get("sha256"):
            errors.append(f"artifact {index} claimed hash does not match the fixture")
        reference = artifact.get("reference")
        if isinstance(reference, str):
            if reference in seen_references:
                errors.append(f"artifact {index} reuses reference {reference}")
            seen_references.add(reference)
        proof = {"reference": reference, "sha256": artifact.get("sha256")}
        _path, _raw, proof_errors = resolve_bound_file(
            proof,
            evidence_path.parent,
            f"artifact {index}",
        )
        errors.extend(proof_errors)
    if len(artifacts) > len(expected):
        errors.append("unexpected artifact proofs are present")
    return errors


def verify_attempt_evidence(
    evidence: Dict[str, Any],
    evidence_path: Path,
    case_meta: Dict[str, Any],
    repetition: int,
    plan_sha256: str,
    route: Dict[str, Any],
    route_sha256: str,
) -> Tuple[Optional[str], Optional[str], List[str]]:
    errors: List[str] = []
    required_keys = {
        "schema_version",
        "suite_sha256",
        "case_sha256",
        "cell_sha256",
        "plan_sha256",
        "route_sha256",
        "route",
        "case_id",
        "repetition",
        "prompt_sha256",
        "fixtures_sha256",
        "response",
        "events",
        "artifacts",
        "execution",
    }
    if set(evidence) != required_keys:
        missing = sorted(required_keys - set(evidence))
        extra = sorted(set(evidence) - required_keys)
        if missing:
            errors.append(f"evidence is missing fields: {missing}")
        if extra:
            errors.append(f"evidence has unrelated fields: {extra}")
    case = case_meta["case"]
    bindings = {
        "schema_version": ATTEMPT_SCHEMA,
        "suite_sha256": case_meta["suite_sha256"],
        "case_sha256": case_meta["case_sha256"],
        "cell_sha256": cell_digest(case_meta, repetition, route_sha256),
        "plan_sha256": plan_sha256,
        "route_sha256": route_sha256,
        "route": route,
        "case_id": case["id"],
        "repetition": repetition,
        "prompt_sha256": case_meta["prompt_sha256"],
        "fixtures_sha256": case_meta["fixtures_sha256"],
    }
    for key, expected in bindings.items():
        if evidence.get(key) != expected:
            errors.append(f"evidence {key} does not match the frozen cell")

    response = evidence.get("response")
    if not isinstance(response, str) or not response.strip():
        errors.append("raw model response is empty")
    else:
        try:
            parsed_response = json.loads(response)
        except json.JSONDecodeError as exc:
            errors.append(f"raw model response is not one JSON value: {exc.msg}")
        else:
            expected_response = case["verifier"]["expected_response"]
            if parsed_response != expected_response:
                errors.append("structured response does not satisfy the frozen verifier")

    events = evidence.get("events")
    expected_events = case["fixtures"]["events"]
    required_ids = case["verifier"]["required_event_ids"]
    if not isinstance(events, list):
        errors.append("events must be an array")
    elif not events:
        errors.append("fixture evidence events are empty")
    else:
        observed_ids = [
            event.get("event_id") if isinstance(event, dict) else None for event in events
        ]
        if observed_ids != required_ids:
            errors.append("event IDs/order do not match the frozen fixture")
        if events != expected_events:
            errors.append("event contents do not match the frozen fixture results")

    expected_artifacts = case["verifier"].get("required_artifacts", [])
    errors.extend(verify_artifacts(evidence, evidence_path, expected_artifacts))
    execution_reference: Optional[str] = None
    execution_sha256: Optional[str] = None
    if isinstance(response, str):
        execution_reference, execution_sha256, execution_errors = verify_execution_trace(
            evidence.get("execution"),
            evidence_path,
            case["id"],
            repetition,
            bindings["cell_sha256"],
            route,
            route_sha256,
            response,
            events,
        )
        errors.extend(execution_errors)
    else:
        errors.append("execution trace cannot bind a non-string response")
    return execution_reference, execution_sha256, errors


def score(
    results: Dict[str, Any],
    results_path: Path,
    suite: Dict[str, Any],
) -> Dict[str, Any]:
    suite_meta, suite_errors = prepare_suite(suite)
    blockers: List[str] = [f"suite: {item}" for item in suite_errors]
    failures: List[Dict[str, Any]] = []
    if results.get("schema_version") != RESULT_SCHEMA:
        blockers.append(f"results schema must be {RESULT_SCHEMA}")
    if results.get("suite_sha256") != suite_meta["suite_sha256"]:
        blockers.append("results suite_sha256 does not match the frozen suite")
    minimum = suite_meta.get("minimum_repetitions")
    repetitions = results.get("repetitions")
    if (
        not isinstance(repetitions, int)
        or isinstance(repetitions, bool)
        or not isinstance(minimum, int)
        or repetitions < minimum
    ):
        blockers.append(f"results repetitions must be an integer >= {minimum or 3}")
        repetitions = minimum if isinstance(minimum, int) else 3
    plan_proof = results.get("plan")
    plan_path, plan_raw, plan_proof_errors = resolve_bound_file(
        plan_proof,
        results_path.parent,
        "truthfulness execution plan",
    )
    blockers.extend(plan_proof_errors)
    plan_sha256 = (
        plan_proof.get("sha256")
        if isinstance(plan_proof, dict) and isinstance(plan_proof.get("sha256"), str)
        else ""
    )
    plan: Optional[Dict[str, Any]] = None
    if plan_raw is not None:
        try:
            parsed_plan = json.loads(plan_raw.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            blockers.append(f"truthfulness execution plan is not UTF-8 JSON: {exc}")
        else:
            if isinstance(parsed_plan, dict):
                plan = parsed_plan
            else:
                blockers.append("truthfulness execution plan is not a JSON object")
    result_route = results.get("route")
    blockers.extend(validate_route(result_route, "results route"))
    route: Dict[str, Any] = result_route if isinstance(result_route, dict) else {}
    route_sha256 = route_digest(route)
    if results.get("route_sha256") != route_sha256:
        blockers.append("results route_sha256 does not match its exact route")
    if plan is not None:
        plan_route, plan_errors = validate_plan(
            plan,
            suite,
            suite_meta,
            repetitions,
        )
        blockers.extend(f"plan: {error}" for error in plan_errors)
        if plan_route != route:
            blockers.append("results route does not match the immutable plan route")
    attempts = results.get("attempts")
    if not isinstance(attempts, list):
        blockers.append("attempts must be an array")
        attempts = []

    case_map = suite_meta["case_map"]
    seen_cells = set()
    seen_references = set()
    seen_hashes = set()
    seen_execution_references = set()
    seen_execution_hashes = set()
    complete_execution_traces = 0
    ignored_assertions = 0
    case_stats = {
        case_id: {"expected": repetitions, "observed": 0, "passed": 0}
        for case_id in case_map
    }
    for index, attempt in enumerate(attempts):
        if not isinstance(attempt, dict):
            blockers.append(f"attempt {index} is not an object")
            continue
        if "deterministic_pass" in attempt:
            ignored_assertions += 1
        case_id = attempt.get("case_id")
        repetition = attempt.get("repetition")
        if (
            case_id not in case_map
            or not isinstance(repetition, int)
            or isinstance(repetition, bool)
            or repetition < 1
            or repetition > repetitions
        ):
            blockers.append(f"attempt {index} identity is invalid")
            continue
        cell = (case_id, repetition)
        if cell in seen_cells:
            blockers.append(f"duplicate attempt {case_id}/{repetition}")
            continue
        seen_cells.add(cell)
        case_stats[case_id]["observed"] += 1
        proof = attempt.get("evidence")
        if isinstance(proof, dict):
            reference = proof.get("reference")
            claimed = proof.get("sha256")
            if isinstance(reference, str):
                if reference in seen_references:
                    blockers.append(
                        f"attempt {case_id}/{repetition} reuses evidence reference {reference}"
                    )
                seen_references.add(reference)
            if isinstance(claimed, str):
                if claimed in seen_hashes:
                    blockers.append(
                        f"attempt {case_id}/{repetition} reuses evidence content hash"
                    )
                seen_hashes.add(claimed)
        evidence_path, raw, proof_errors = resolve_bound_file(
            proof,
            results_path.parent,
            f"attempt {case_id}/{repetition} evidence",
        )
        attempt_errors = list(proof_errors)
        evidence: Optional[Dict[str, Any]] = None
        if raw is not None:
            if not raw.strip():
                attempt_errors.append("attempt evidence file is empty")
            else:
                try:
                    parsed = json.loads(raw.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError) as exc:
                    attempt_errors.append(f"attempt evidence is not valid UTF-8 JSON: {exc}")
                else:
                    if isinstance(parsed, dict):
                        evidence = parsed
                    else:
                        attempt_errors.append("attempt evidence is not a JSON object")
        if evidence is not None and evidence_path is not None:
            execution_reference, execution_sha256, verification_errors = (
                verify_attempt_evidence(
                    evidence,
                    evidence_path,
                    case_map[case_id],
                    repetition,
                    plan_sha256,
                    route,
                    route_sha256,
                )
            )
            attempt_errors.extend(verification_errors)
            if execution_reference is not None:
                if execution_reference in seen_execution_references:
                    blockers.append(
                        f"attempt {case_id}/{repetition} reuses execution trace reference"
                    )
                seen_execution_references.add(execution_reference)
            if execution_sha256 is not None:
                if execution_sha256 in seen_execution_hashes:
                    blockers.append(
                        f"attempt {case_id}/{repetition} reuses execution trace content hash"
                    )
                seen_execution_hashes.add(execution_sha256)
        if attempt_errors:
            failures.append(
                {
                    "case_id": case_id,
                    "repetition": repetition,
                    "reasons": attempt_errors,
                }
            )
        else:
            case_stats[case_id]["passed"] += 1
            complete_execution_traces += 1

    expected_cells = {
        (case_id, repetition)
        for case_id in case_map
        for repetition in range(1, repetitions + 1)
    }
    missing = sorted(expected_cells - seen_cells)
    if missing:
        blockers.append(f"missing {len(missing)} required case/repetition cells")
    extra = sorted(seen_cells - expected_cells)
    if extra:
        blockers.append(f"observed {len(extra)} unexpected case/repetition cells")
    passed = not blockers and not failures
    return {
        "schema_version": SCORE_SCHEMA,
        "passed": passed,
        "suite_sha256": suite_meta["suite_sha256"],
        "plan_sha256": plan_sha256,
        "route": route,
        "route_sha256": route_sha256,
        "repetitions": repetitions,
        "case_count": len(case_map),
        "expected_cells": len(expected_cells),
        "observed_cells": len(seen_cells),
        "case_results": case_stats,
        "execution_trace_count": complete_execution_traces,
        "execution_attribution_complete": (
            complete_execution_traces == len(expected_cells)
        ),
        "blockers": blockers,
        "deterministic_failures": failures,
        "asserted_deterministic_pass_ignored": True,
        "ignored_assertion_count": ignored_assertions,
        "judge_scores_affect_pass": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("results", type=Path)
    parser.add_argument(
        "--suite",
        type=Path,
        default=Path(__file__).resolve().parent.parent
        / "references"
        / "truthfulness-suite-v1.json",
    )
    parser.add_argument("--json", dest="json_out", type=Path)
    args = parser.parse_args()
    try:
        results = read_json_object(args.results)
        suite = read_json_object(args.suite)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    report = score(results, args.results, suite)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.json_out:
        try:
            args.json_out.parent.mkdir(parents=True, exist_ok=True)
            args.json_out.write_text(rendered, encoding="utf-8")
        except OSError as exc:
            print(f"error: could not write {args.json_out}: {exc}", file=sys.stderr)
            return 2
    else:
        sys.stdout.write(rendered)
    return 0 if report["passed"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
