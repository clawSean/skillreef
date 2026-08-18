#!/usr/bin/env python3
"""Exact-route adversarial tests for local cache admission planning/scoring."""

from __future__ import annotations

import copy
import hashlib
import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BUILDER = ROOT / "scripts" / "build_local_cache_admission_plan.py"
VALIDATOR = ROOT / "scripts" / "validate_local_cache_admission.py"
HASH = "sha256:" + "a" * 64
REVISION = "a" * 40
OPENCLAW = "b" * 40


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def base(
    runtime: str, version: str, *features: str, mlx: str = "0.32.1",
    defaults: bool = True,
) -> list[str]:
    feature_set = set(features)
    if defaults and not feature_set & {"text-only", "multimodal"}:
        feature_set.add("text-only")
    if defaults and not feature_set & {"isolated-service", "shared-service"}:
        feature_set.add("isolated-service")
    if defaults and not feature_set & {"serial-service", "batched-service"}:
        feature_set.add("serial-service")
    args = [
        "--runtime", runtime, "--runtime-version", version, "--mlx-version", mlx,
        "--provider", "local-exact-provider", "--model", "exact-model",
        "--loaded-model", "mlx-community/exact-model", "--model-revision", REVISION,
        "--openclaw-version", "2026.7.1-custom",
        "--openclaw-commit", OPENCLAW,
        "--architecture-fingerprint", HASH,
        "--template-fingerprint", HASH,
        "--parser-fingerprint", HASH,
        "--cache-policy-fingerprint", HASH,
        "--cache-layout-fingerprint", HASH,
    ]
    for feature in sorted(feature_set):
        args += ["--feature", feature]
    return args


def run_builder(root: Path, label: str, expected: int, args: list[str]) -> dict:
    out = root / f"{label}-plan.json"
    result = subprocess.run(
        [sys.executable, str(BUILDER), *args, "--out", str(out)],
        text=True, capture_output=True, check=False,
    )
    if result.returncode != expected:
        raise AssertionError(
            f"{label}: expected {expected}, got {result.returncode}\n"
            f"stdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
    return json.loads(out.read_text(encoding="utf-8"))


def proof(path: Path, kind: str = "test-proof") -> dict:
    return {"kind": kind, "reference": path.name, "sha256": sha256(path)}


def build_results(root: Path, plan_path: Path, plan: dict) -> tuple[Path, dict]:
    architecture_path = root / "architecture.json"
    route_path = root / "route.json"
    write(
        architecture_path,
        {
            "schema_version": "clawgauge.local-model-architecture.v1",
            "model": plan["provenance"]["model"],
            "loaded_model": plan["provenance"]["loaded_model"],
            "model_revision": plan["provenance"]["model_revision"],
            "architecture_fingerprint": plan["provenance"]["architecture_fingerprint"],
            "features": plan["provenance"]["features"],
        },
    )
    route = {
        "schema_version": "clawgauge.local-route-observation.v1",
        **plan["provenance"],
        "requested_provider": plan["provenance"]["provider"],
        "requested_model": plan["provenance"]["model"],
        "observed_provider": plan["provenance"]["provider"],
        "observed_model": plan["provenance"]["model"],
        "response_model": plan["provenance"]["model"],
        "fallback_used": False,
        "backend_pid": 1234,
        "backend_started_at": "2026-08-18T00:00:00Z",
        "runtime_id": "runtime-1",
        "cache_epoch": "epoch-1",
    }
    write(route_path, route)
    case_rows = []
    for index, case in enumerate(plan["cases"]):
        evidence_path = root / f"case-{index}.json"
        write(evidence_path, {"case": case["id"], "passed": True})
        case_rows.append({"id": case["id"], "status": "pass", "evidence": [proof(evidence_path)]})
    results = {
        "schema_version": "clawgauge.local-cache-admission-results.v1",
        "plan_fingerprint": plan["plan_fingerprint"],
        "plan_sha256": sha256(plan_path),
        "provenance": plan["provenance"],
        "architecture_manifest_proof": proof(
            architecture_path, "clawgauge-local-architecture-manifest"
        ),
        "openclaw_route_proof": proof(
            route_path, "clawgauge-local-route-observation"
        ),
        "cases": case_rows,
        "blockers": [],
    }
    results_path = root / "results.json"
    write(results_path, results)
    return results_path, results


def run_validator(root: Path, label: str, plan_path: Path, results: dict, expected: int) -> dict:
    results_path = root / f"{label}-results.json"
    score_path = root / f"{label}-score.json"
    write(results_path, results)
    completed = subprocess.run(
        [
            sys.executable, str(VALIDATOR), str(plan_path), str(results_path),
            "--artifact-root", str(root), "--out", str(score_path),
        ],
        text=True, capture_output=True, check=False,
    )
    if completed.returncode != expected:
        raise AssertionError(
            f"{label}: expected {expected}, got {completed.returncode}\n"
            f"stdout:\n{completed.stdout}\nstderr:\n{completed.stderr}"
        )
    return json.loads(score_path.read_text(encoding="utf-8"))


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="clawgauge-cache-admission-") as raw:
        root = Path(raw)

        old = run_builder(root, "old", 2, base("mlx-vlm", "0.6.14", "standard-kv"))
        assert not old["ok_to_execute"]
        assert any("0.6.15" in item for item in old["blockers"])
        checks += 2

        missing_arch = run_builder(root, "missing-architecture", 2, base("mlx-vlm", "0.6.15"))
        assert any("exactly one structural" in item for item in missing_arch["blockers"])
        checks += 1

        for label, features, expected_text in (
            ("missing-modality", ("standard-kv", "isolated-service", "serial-service"), "modality"),
            ("missing-scope", ("standard-kv", "text-only", "serial-service"), "service scope"),
            ("missing-batching", ("standard-kv", "text-only", "isolated-service"), "batching mode"),
        ):
            plan = run_builder(
                root, label, 2,
                base("mlx-vlm", "0.6.15", *features, defaults=False),
            )
            assert any(expected_text in item for item in plan["blockers"])
            checks += 1

        ambiguous = run_builder(
            root, "ambiguous", 2,
            base("mlx-vlm", "0.6.15", "standard-kv", "hybrid-recurrent"),
        )
        assert any("exactly one structural" in item for item in ambiguous["blockers"])
        checks += 1

        hybrid = run_builder(
            root, "hybrid", 0,
            base(
                "mlx-vlm", "0.6.15", "hybrid-recurrent", "multimodal",
                "shared-service", "batched-service",
            ),
        )
        plan_path = root / "hybrid-plan.json"
        ids = {case["id"] for case in hybrid["cases"]}
        assert hybrid["network_calls_performed"] == 0
        assert {
            "stateful-branch-replay", "media-key-isolation",
            "tenant-and-eviction-isolation", "batch-parity",
        } <= ids
        assert "cache-qualified" in hybrid["claim_not_granted"]
        checks += 3

        _results_path, results = build_results(root, plan_path, hybrid)
        passed = run_validator(root, "pass", plan_path, results, 0)
        assert passed["passed"] is True
        assert passed["claim_granted"] == "cache-qualified"
        assert passed["blockers"] == []
        checks += 3

        missing = copy.deepcopy(results)
        missing["cases"].pop()
        assert run_validator(root, "missing-case", plan_path, missing, 2)["passed"] is False
        checks += 1

        duplicate = copy.deepcopy(results)
        duplicate["cases"].append(copy.deepcopy(duplicate["cases"][0]))
        score = run_validator(root, "duplicate-case", plan_path, duplicate, 2)
        assert any("duplicate" in item for item in score["blockers"])
        checks += 1

        tampered = copy.deepcopy(results)
        evidence_path = root / tampered["cases"][0]["evidence"][0]["reference"]
        evidence_path.write_text("tampered\n", encoding="utf-8")
        score = run_validator(root, "tampered", plan_path, tampered, 2)
        assert any("hash mismatch" in item for item in score["blockers"])
        checks += 1
        write(evidence_path, {"case": hybrid["cases"][0]["id"], "passed": True})
        results["cases"][0]["evidence"][0]["sha256"] = sha256(evidence_path)

        stale = copy.deepcopy(results)
        route_path = root / stale["openclaw_route_proof"]["reference"]
        route = json.loads(route_path.read_text(encoding="utf-8"))
        route["cache_epoch"] = ""
        write(route_path, route)
        stale["openclaw_route_proof"]["sha256"] = sha256(route_path)
        score = run_validator(root, "stale-epoch", plan_path, stale, 2)
        assert any("cache_epoch" in item for item in score["blockers"])
        checks += 1
        route["cache_epoch"] = "epoch-1"
        write(route_path, route)
        results["openclaw_route_proof"]["sha256"] = sha256(route_path)

        fallback = copy.deepcopy(results)
        route["fallback_used"] = True
        write(route_path, route)
        fallback["openclaw_route_proof"]["sha256"] = sha256(route_path)
        score = run_validator(root, "fallback", plan_path, fallback, 2)
        assert any("fallback" in item for item in score["blockers"])
        checks += 1
        route["fallback_used"] = False
        write(route_path, route)
        results["openclaw_route_proof"]["sha256"] = sha256(route_path)

        wrong_route = copy.deepcopy(results)
        route["observed_provider"] = "wrong-provider"
        write(route_path, route)
        wrong_route["openclaw_route_proof"]["sha256"] = sha256(route_path)
        score = run_validator(root, "wrong-observed-provider", plan_path, wrong_route, 2)
        assert any("requested/observed/response" in item for item in score["blockers"])
        checks += 1
        route["observed_provider"] = hybrid["provenance"]["provider"]
        write(route_path, route)
        results["openclaw_route_proof"]["sha256"] = sha256(route_path)

        wrong_loaded = copy.deepcopy(results)
        route["loaded_model"] = "mlx-community/wrong-model"
        write(route_path, route)
        wrong_loaded["openclaw_route_proof"]["sha256"] = sha256(route_path)
        score = run_validator(root, "wrong-loaded-model", plan_path, wrong_loaded, 2)
        assert any("frozen plan" in item for item in score["blockers"])
        checks += 1
        route["loaded_model"] = hybrid["provenance"]["loaded_model"]
        write(route_path, route)
        results["openclaw_route_proof"]["sha256"] = sha256(route_path)

        for case_id in ("media-key-isolation", "tenant-and-eviction-isolation"):
            failed = copy.deepcopy(results)
            next(item for item in failed["cases"] if item["id"] == case_id)["status"] = "fail"
            score = run_validator(root, f"failed-{case_id}", plan_path, failed, 2)
            assert any(case_id in item for item in score["blockers"])
            checks += 1

        lm = run_builder(root, "lm", 0, base("mlx-lm", "0.31.3", "standard-kv", "shared-service"))
        assert any("not a universal hard cap" in item for item in lm["warnings"])
        checks += 1

    print(f"ClawGauge local cache admission tests: PASS ({checks} assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
