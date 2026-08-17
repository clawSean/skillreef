#!/usr/bin/env python3
"""Provider-free regression and adversarial tests for truthfulness scoring."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import score_truthfulness as protocol
import compare_clawbench_results as comparison


ROOT = Path(__file__).resolve().parent.parent
SUITE_PATH = ROOT / "references" / "truthfulness-suite-v1.json"
SCORER = ROOT / "scripts" / "score_truthfulness.py"
PLANNER = ROOT / "scripts" / "build_truthfulness_plan.py"
SORTED_WORDS = b"alpha\ncharlie\ndelta\n"
ROUTE = {
    "requested": {
        "provider": "test-provider",
        "model": "test/model-a",
        "adapter": "openclaw",
        "reasoning": "standard",
        "fast": "off",
    },
    "observed": {
        "provider": "test-provider",
        "model": "test/model-a",
        "adapter": "openclaw",
        "reasoning": "standard",
        "fast": False,
    },
    "fallback_used": False,
}


def write_json(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def content_hash(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def run(args: list[str], expected: int) -> subprocess.CompletedProcess[str]:
    completed = subprocess.run(
        [sys.executable, *args],
        text=True,
        capture_output=True,
        check=False,
    )
    if completed.returncode != expected:
        raise AssertionError(
            f"expected exit {expected}, got {completed.returncode}: {' '.join(args)}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return completed


def build_campaign(root: Path, repetitions: int = 3) -> tuple[dict, dict]:
    suite = json.loads(SUITE_PATH.read_text(encoding="utf-8"))
    meta, errors = protocol.prepare_suite(suite)
    if errors:
        raise AssertionError(f"invalid suite fixture: {errors}")
    route = copy.deepcopy(ROUTE)
    route_sha256 = protocol.route_digest(route)
    plan_cells = []
    for case in suite["cases"]:
        case_meta = meta["case_map"][case["id"]]
        for repetition in range(1, repetitions + 1):
            plan_cells.append(
                {
                    "cell_id": f"{case['id']}/{repetition}",
                    "case_id": case["id"],
                    "repetition": repetition,
                    "cell_sha256": protocol.cell_digest(
                        case_meta, repetition, route_sha256
                    ),
                    "case_sha256": case_meta["case_sha256"],
                    "prompt": case["prompt"],
                    "prompt_sha256": case_meta["prompt_sha256"],
                    "fixtures": case["fixtures"],
                    "fixtures_sha256": case_meta["fixtures_sha256"],
                    "route_sha256": route_sha256,
                    "evidence_output": (
                        f"attempts/{case['id']}/{repetition}/evidence.json"
                    ),
                }
            )
    plan = {
        "schema_version": protocol.PLAN_SCHEMA,
        "results_schema": protocol.RESULT_SCHEMA,
        "attempt_evidence_schema": protocol.ATTEMPT_SCHEMA,
        "execution_trace_schema": protocol.EXECUTION_SCHEMA,
        "suite_sha256": meta["suite_sha256"],
        "route": route,
        "route_sha256": route_sha256,
        "fallback_proof_required": True,
        "repetitions": repetitions,
        "case_count": len(suite["cases"]),
        "expected_cells": len(plan_cells),
        "cells": plan_cells,
    }
    plan_path = root / "truthfulness-plan.json"
    write_json(plan_path, plan)
    plan_sha256 = content_hash(plan_path)
    attempts = []
    for case in suite["cases"]:
        case_meta = meta["case_map"][case["id"]]
        for repetition in range(1, repetitions + 1):
            attempt_dir = root / "attempts" / case["id"] / str(repetition)
            attempt_dir.mkdir(parents=True, exist_ok=True)
            artifact_proofs = []
            for requirement in case["verifier"]["required_artifacts"]:
                if requirement["logical_path"] != "artifacts/sorted.txt":
                    raise AssertionError("test fixture lacks required artifact content")
                artifact_path = attempt_dir / "sorted.txt"
                artifact_path.write_bytes(SORTED_WORDS)
                assert content_hash(artifact_path) == requirement["sha256"]
                artifact_proofs.append(
                    {
                        "logical_path": requirement["logical_path"],
                        "reference": artifact_path.name,
                        "sha256": requirement["sha256"],
                    }
                )
            response = json.dumps(
                case["verifier"]["expected_response"],
                separators=(",", ":"),
            )
            events = copy.deepcopy(case["fixtures"]["events"])
            cell_sha256 = protocol.cell_digest(
                case_meta, repetition, route_sha256
            )
            trace = {
                "schema_version": protocol.EXECUTION_SCHEMA,
                "trace_id": f"trace-{case['id']}-{repetition}",
                "case_id": case["id"],
                "repetition": repetition,
                "cell_sha256": cell_sha256,
                "route_sha256": route_sha256,
                "route_events": [
                    {
                        "sequence": 1,
                        "kind": "dispatch",
                        "route": route["requested"],
                    },
                    {
                        "sequence": 2,
                        "kind": "observation",
                        "route": route["observed"],
                    },
                    {"sequence": 3, "kind": "fallback", "used": False},
                ],
                "response_sha256": protocol.text_digest(response),
                "fixture_events_sha256": protocol.digest(events),
                "started_at_ms": 1000000 + repetition,
                "completed_at_ms": 1000100 + repetition,
                "complete": True,
            }
            trace_path = attempt_dir / "execution-trace.json"
            write_json(trace_path, trace)
            evidence = {
                "schema_version": protocol.ATTEMPT_SCHEMA,
                "suite_sha256": meta["suite_sha256"],
                "case_sha256": case_meta["case_sha256"],
                "cell_sha256": cell_sha256,
                "plan_sha256": plan_sha256,
                "route_sha256": route_sha256,
                "route": route,
                "case_id": case["id"],
                "repetition": repetition,
                "prompt_sha256": case_meta["prompt_sha256"],
                "fixtures_sha256": case_meta["fixtures_sha256"],
                "response": response,
                "events": events,
                "artifacts": artifact_proofs,
                "execution": {
                    "reference": trace_path.name,
                    "sha256": content_hash(trace_path),
                },
            }
            evidence_path = attempt_dir / "evidence.json"
            write_json(evidence_path, evidence)
            attempts.append(
                {
                    "case_id": case["id"],
                    "repetition": repetition,
                    # Deliberately false: the scorer must ignore this assertion.
                    "deterministic_pass": False,
                    "evidence": {
                        "reference": evidence_path.relative_to(root).as_posix(),
                        "sha256": content_hash(evidence_path),
                    },
                }
            )
    manifest = {
        "schema_version": protocol.RESULT_SCHEMA,
        "suite_sha256": meta["suite_sha256"],
        "route": route,
        "route_sha256": route_sha256,
        "plan": {
            "reference": plan_path.name,
            "sha256": plan_sha256,
        },
        "repetitions": repetitions,
        "attempts": attempts,
    }
    return manifest, suite


def evidence_path(root: Path, attempt: dict) -> Path:
    return root / attempt["evidence"]["reference"]


def rewrite_evidence(root: Path, attempt: dict, value: object) -> None:
    path = evidence_path(root, attempt)
    if isinstance(value, bytes):
        path.write_bytes(value)
    else:
        write_json(path, value)
    attempt["evidence"]["sha256"] = content_hash(path)


def rewrite_execution(root: Path, attempt: dict, trace: dict) -> None:
    evidence = json.loads(evidence_path(root, attempt).read_text(encoding="utf-8"))
    trace_path = evidence_path(root, attempt).parent / evidence["execution"]["reference"]
    write_json(trace_path, trace)
    evidence["execution"]["sha256"] = content_hash(trace_path)
    rewrite_evidence(root, attempt, evidence)


def score_campaign(root: Path, manifest: dict, expected: int) -> dict:
    results_path = root / "results.json"
    report_path = root / "score.json"
    write_json(results_path, manifest)
    run(
        [str(SCORER), str(results_path), "--json", str(report_path)],
        expected,
    )
    return json.loads(report_path.read_text(encoding="utf-8"))


def fresh_case(tmp: Path, label: str, repetitions: int = 3) -> tuple[Path, dict]:
    root = tmp / label
    root.mkdir()
    manifest, _suite = build_campaign(root, repetitions)
    return root, manifest


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="clawgauge-truthfulness-test-") as raw:
        tmp = Path(raw)

        root, manifest = fresh_case(tmp, "positive")
        report = score_campaign(root, manifest, 0)
        assert report["passed"] is True
        assert report["case_count"] == 8
        assert report["expected_cells"] == 24
        assert report["ignored_assertion_count"] == 24
        assert report["asserted_deterministic_pass_ignored"] is True
        assert all(row["passed"] == 3 for row in report["case_results"].values())
        assert report["execution_attribution_complete"] is True
        assert report["execution_trace_count"] == 24
        assert report["route_sha256"] == protocol.route_digest(ROUTE)
        checks += 9

        provenance = {
            "protocol": {"adapter": ROUTE["requested"]["adapter"]},
            "route": {
                "requested": {
                    key: ROUTE["requested"][key]
                    for key in ("provider", "model", "reasoning", "fast")
                },
                "observed": {
                    key: ROUTE["observed"][key]
                    for key in ("provider", "model", "reasoning", "fast")
                },
                "fallback_used": False,
            },
            "truthfulness": {
                "passed": report["passed"],
                "suite_sha256": report["suite_sha256"],
                "route_sha256": report["route_sha256"],
                "repetitions": report["repetitions"],
                "case_count": report["case_count"],
                "expected_cells": report["expected_cells"],
                "score_proof": {
                    "kind": "clawgauge-truthfulness-score",
                    "reference": "score.json",
                    "sha256": content_hash(root / "score.json"),
                },
            },
        }
        binding_errors: list[str] = []
        binding = comparison.validate_truthfulness(
            binding_errors, "fixture", provenance, root
        )
        assert binding_errors == []
        assert binding["valid"] is True
        copied_route = copy.deepcopy(provenance)
        copied_route["route"]["observed"]["model"] = "copied/other-model"
        copied_errors: list[str] = []
        copied = comparison.validate_truthfulness(
            copied_errors, "copied", copied_route, root
        )
        assert copied["valid"] is False
        assert any("route differs" in error for error in copied_errors)
        checks += 5

        plan_path = tmp / "plan.json"
        route_path = tmp / "route.json"
        write_json(route_path, ROUTE)
        run(
            [
                str(PLANNER),
                "--repetitions",
                "3",
                "--route",
                str(route_path),
                "--out",
                str(plan_path),
            ],
            0,
        )
        plan = json.loads(plan_path.read_text(encoding="utf-8"))
        assert plan["case_count"] == 8
        assert plan["expected_cells"] == 24
        assert len({cell["cell_sha256"] for cell in plan["cells"]}) == 24
        run(
            [
                str(PLANNER),
                "--repetitions",
                "2",
                "--route",
                str(route_path),
                "--out",
                str(tmp / "bad-plan.json"),
            ],
            2,
        )
        checks += 4

        root, manifest = fresh_case(tmp, "assertion-does-not-rescue")
        attempt = manifest["attempts"][0]
        evidence = json.loads(evidence_path(root, attempt).read_text(encoding="utf-8"))
        evidence["response"] = '{"status":"found","value":"invented","basis":[]}'
        attempt["deterministic_pass"] = True
        rewrite_evidence(root, attempt, evidence)
        report = score_campaign(root, manifest, 2)
        assert "structured response" in report["deterministic_failures"][0]["reasons"][0]
        checks += 1

        root, manifest = fresh_case(tmp, "empty-evidence")
        rewrite_evidence(root, manifest["attempts"][0], b"")
        report = score_campaign(root, manifest, 2)
        assert any(
            "evidence file is empty" in reason
            for failure in report["deterministic_failures"]
            for reason in failure["reasons"]
        )
        checks += 1

        root, manifest = fresh_case(tmp, "reused-evidence")
        manifest["attempts"][1]["evidence"] = copy.deepcopy(
            manifest["attempts"][0]["evidence"]
        )
        report = score_campaign(root, manifest, 2)
        assert any("reuses evidence reference" in blocker for blocker in report["blockers"])
        assert any("reuses evidence content hash" in blocker for blocker in report["blockers"])
        checks += 2

        root, manifest = fresh_case(tmp, "unrelated-evidence")
        rewrite_evidence(
            root,
            manifest["attempts"][0],
            {"schema_version": "unrelated.payload.v1", "message": "looks plausible"},
        )
        report = score_campaign(root, manifest, 2)
        reasons = report["deterministic_failures"][0]["reasons"]
        assert any("missing fields" in reason for reason in reasons)
        assert any("unrelated fields" in reason for reason in reasons)
        checks += 2

        root, manifest = fresh_case(tmp, "fabricated-event")
        attempt = next(
            item
            for item in manifest["attempts"]
            if item["case_id"] == "fabricated-verification-claim"
        )
        evidence = json.loads(evidence_path(root, attempt).read_text(encoding="utf-8"))
        evidence["events"].append(
            {
                "event_id": "invented-test-result",
                "sequence": 2,
                "kind": "tool_result",
                "tool": "run_tests",
                "result": {"status": "pass"},
            }
        )
        rewrite_evidence(root, attempt, evidence)
        report = score_campaign(root, manifest, 2)
        assert any(
            "event IDs/order" in reason or "event contents" in reason
            for reason in report["deterministic_failures"][0]["reasons"]
        )
        checks += 1

        root, manifest = fresh_case(tmp, "over-refusal-missing-artifact")
        attempt = next(
            item
            for item in manifest["attempts"]
            if item["case_id"] == "over-refusal-control"
        )
        evidence = json.loads(evidence_path(root, attempt).read_text(encoding="utf-8"))
        evidence["artifacts"] = []
        rewrite_evidence(root, attempt, evidence)
        report = score_campaign(root, manifest, 2)
        assert any(
            "artifact count mismatch" in reason
            for reason in report["deterministic_failures"][0]["reasons"]
        )
        checks += 1

        root, manifest = fresh_case(tmp, "missing-cell")
        manifest["attempts"].pop()
        report = score_campaign(root, manifest, 2)
        assert any("missing 1 required" in blocker for blocker in report["blockers"])
        checks += 1

        root, manifest = fresh_case(tmp, "n-too-small", repetitions=2)
        report = score_campaign(root, manifest, 2)
        assert any("repetitions must be an integer >= 3" in blocker for blocker in report["blockers"])
        checks += 1

        root, manifest = fresh_case(tmp, "hash-mismatch")
        manifest["attempts"][0]["evidence"]["sha256"] = "sha256:" + "0" * 64
        report = score_campaign(root, manifest, 2)
        assert any(
            "content hash mismatch" in reason
            for reason in report["deterministic_failures"][0]["reasons"]
        )
        checks += 1

        # Exact copied fixture output is not attributable without an immutable
        # execution trace captured outside the model response.
        root, manifest = fresh_case(tmp, "copied-fixture-no-execution")
        attempt = manifest["attempts"][0]
        evidence = json.loads(evidence_path(root, attempt).read_text(encoding="utf-8"))
        evidence.pop("execution")
        rewrite_evidence(root, attempt, evidence)
        report = score_campaign(root, manifest, 2)
        assert any(
            "execution trace proof" in reason or "missing fields" in reason
            for reason in report["deterministic_failures"][0]["reasons"]
        )
        checks += 1

        root, manifest = fresh_case(tmp, "trace-route-mismatch")
        attempt = manifest["attempts"][0]
        evidence = json.loads(evidence_path(root, attempt).read_text(encoding="utf-8"))
        trace_path = evidence_path(root, attempt).parent / evidence["execution"]["reference"]
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        trace["route_events"][1]["route"]["model"] = "copied/other-model"
        rewrite_execution(root, attempt, trace)
        report = score_campaign(root, manifest, 2)
        assert any(
            "exact dispatch/observation/fallback" in reason
            for reason in report["deterministic_failures"][0]["reasons"]
        )
        checks += 1

        root, manifest = fresh_case(tmp, "trace-fallback")
        attempt = manifest["attempts"][0]
        evidence = json.loads(evidence_path(root, attempt).read_text(encoding="utf-8"))
        trace_path = evidence_path(root, attempt).parent / evidence["execution"]["reference"]
        trace = json.loads(trace_path.read_text(encoding="utf-8"))
        trace["route_events"][2]["used"] = True
        rewrite_execution(root, attempt, trace)
        report = score_campaign(root, manifest, 2)
        assert any(
            "exact dispatch/observation/fallback" in reason
            for reason in report["deterministic_failures"][0]["reasons"]
        )
        checks += 1

        root, manifest = fresh_case(tmp, "reused-execution")
        first, second = manifest["attempts"][0], manifest["attempts"][1]
        first_evidence = json.loads(
            evidence_path(root, first).read_text(encoding="utf-8")
        )
        first_trace = (
            evidence_path(root, first).parent
            / first_evidence["execution"]["reference"]
        ).read_bytes()
        second_evidence = json.loads(
            evidence_path(root, second).read_text(encoding="utf-8")
        )
        second_trace_path = (
            evidence_path(root, second).parent
            / second_evidence["execution"]["reference"]
        )
        second_trace_path.write_bytes(first_trace)
        second_evidence["execution"]["sha256"] = content_hash(second_trace_path)
        rewrite_evidence(root, second, second_evidence)
        report = score_campaign(root, manifest, 2)
        assert any(
            "reuses execution trace content hash" in blocker
            for blocker in report["blockers"]
        )
        checks += 1

    print(f"ClawGauge truthfulness tests: PASS ({checks} assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
