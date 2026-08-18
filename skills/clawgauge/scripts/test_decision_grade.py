#!/usr/bin/env python3
"""Provider-free adversarial tests for decision-grade evidence gates."""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
SCRIPT = ROOT / "scripts" / "compare_clawbench_results.py"


def load_module():
    spec = importlib.util.spec_from_file_location("clawgauge_compare", SCRIPT)
    if spec is None or spec.loader is None:
        raise AssertionError(f"could not import {SCRIPT}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def write(path: Path, value: object) -> None:
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def sha256(path: Path) -> str:
    return "sha256:" + hashlib.sha256(path.read_bytes()).hexdigest()


def proof(path: Path, kind: str) -> dict:
    return {"kind": kind, "reference": path.name, "sha256": sha256(path)}


def qa_record(model: str, scenarios: set[str]) -> dict:
    return {
        "model": model,
        "gate_status": "pass",
        "provider_modes": ["live-frontier"],
        "fallback_state": "disabled",
        "fast_modes_effective": [False],
        "passed": 10,
        "failed": 0,
        "stalled": 0,
        "blocked": 0,
        "skipped": 0,
        "scenarios": {item: {"status": "pass"} for item in sorted(scenarios)},
        "attempts": [{
            "mode": "personal-agent-profile",
            "profile": "personal-agent",
            "evidence_kind": "profile",
            "blockers": [],
        }],
    }


def main() -> int:
    compare = load_module()
    checks = 0
    complete_facts = {
        "shellbench_coverage": "core-19",
        "truthfulness_comparable": True,
        "qa_comparable": True,
        "local_cache_admission_ready": True,
    }
    passed, requirements, reason = compare.decision_grade_status([], 3, complete_facts)
    assert passed and all(requirements.values()) and "all passed" in reason
    checks += 3

    cases = [
        (["blocked"], 3, complete_facts, "protocol_unblocked"),
        ([], 2, complete_facts, "n_at_least_3"),
        ([], 3, {**complete_facts, "shellbench_coverage": "pinned-release:standard-mac"}, "core_19_coverage"),
        ([], 3, {**complete_facts, "truthfulness_comparable": False}, "truthfulness_comparable"),
        ([], 3, {**complete_facts, "qa_comparable": False}, "personal_agent_qa_comparable"),
        ([], 3, {**complete_facts, "local_cache_admission_ready": False}, "local_cache_admission_ready"),
    ]
    for blockers, runs, facts, missing in cases:
        ok, gates, _ = compare.decision_grade_status(blockers, runs, facts)
        assert not ok and gates[missing] is False
        checks += 1

    with tempfile.TemporaryDirectory(prefix="clawgauge-decision-grade-") as raw:
        root = Path(raw)
        baseline_model = "local/baseline"
        candidate_model = "local/candidate"
        score = {
            "schema_version": 3,
            "comparison_status": "comparable",
            "comparison_blockers": [],
            "models": [
                qa_record(baseline_model, compare.PERSONAL_AGENT_SCENARIOS),
                qa_record(candidate_model, compare.PERSONAL_AGENT_SCENARIOS),
            ],
        }
        qa_path = root / "qa-score.json"
        write(qa_path, score)
        qa_prov = {
            "route": {"observed": {"model": baseline_model, "fast": False}},
            "qa": {
                "passed": True,
                "profile": "personal-agent",
                "scenario_count": 10,
                "model": baseline_model,
                "fast_mode_effective": False,
                "score_proof": proof(qa_path, "clawgauge-qa-scorecard"),
            },
        }
        blockers: list[str] = []
        qa = compare.validate_qa(blockers, "baseline", qa_prov, root)
        assert not blockers and qa["valid"] and qa["passed"]
        checks += 3

        failed_retry = copy.deepcopy(score)
        failed_retry["models"][0]["attempts"].append({
            "mode": "personal-agent-profile",
            "profile": "personal-agent",
            "evidence_kind": "profile",
            "blockers": ["retry failed"],
        })
        write(qa_path, failed_retry)
        retry_prov = copy.deepcopy(qa_prov)
        retry_prov["qa"]["score_proof"] = proof(qa_path, "clawgauge-qa-scorecard")
        blockers = []
        assert compare.validate_qa(blockers, "baseline", retry_prov, root)["valid"] is False
        assert any("attempt evidence" in item for item in blockers)
        checks += 2

        write(qa_path, score)
        tampered = copy.deepcopy(qa_prov)
        tampered["qa"]["score_proof"]["sha256"] = "sha256:" + "0" * 64
        blockers = []
        assert compare.validate_qa(blockers, "baseline", tampered, root)["valid"] is False
        assert any("hash mismatch" in item for item in blockers)
        checks += 2

        mismatched = copy.deepcopy(qa_prov)
        mismatched["qa"]["model"] = candidate_model
        blockers = []
        assert compare.validate_qa(blockers, "baseline", mismatched, root)["valid"] is False
        checks += 1

        fingerprint = "sha256:" + "a" * 64
        openclaw_commit = "b" * 40
        baseline_provider = "local-qwen-coder-next"
        admission_score = {
            "schema_version": "clawgauge.local-cache-admission-score.v1",
            "passed": True,
            "claim_granted": "cache-qualified",
            "blockers": [],
            "plan_fingerprint": "sha256:" + "c" * 64,
            "case_count": 5,
            "provenance": {
                "runtime": "mlx-lm",
                "runtime_version": "0.31.3",
                "provider": baseline_provider,
                "model": baseline_model,
                "openclaw_commit": openclaw_commit,
                "cache_policy_fingerprint": fingerprint,
                "features": ["hybrid-recurrent"],
                "architecture_fingerprint": fingerprint,
                "template_fingerprint": fingerprint,
                "parser_fingerprint": fingerprint,
                "cache_layout_fingerprint": fingerprint,
            },
        }
        admission_path = root / "admission-score.json"
        write(admission_path, admission_score)
        cache = {
            "runtime": {"visibility": "known", "name": "mlx-lm", "version": "0.31.3"},
            "configuration": {"enabled": True, "fingerprint": fingerprint},
            "admission": {
                "passed": True,
                "plan_fingerprint": admission_score["plan_fingerprint"],
                "case_count": 5,
                "score_proof": proof(
                    admission_path, "clawgauge-local-cache-admission-score"
                ),
            },
        }
        route_prov = {
            "route": {
                "observed": {
                    "provider": baseline_provider,
                    "model": baseline_model,
                }
            },
            "openclaw": {"commit": openclaw_commit},
        }
        blockers = []
        admission = compare.validate_local_admission(
            blockers, "baseline", route_prov, cache, root
        )
        assert not blockers and admission["required"] and admission["passed"]
        checks += 3

        absent = copy.deepcopy(cache)
        absent.pop("admission")
        blockers = []
        admission = compare.validate_local_admission(
            blockers, "baseline", route_prov, absent, root
        )
        assert admission["required"] and not admission["available"] and not blockers
        checks += 3

        wrong_provenance = copy.deepcopy(admission_score)
        wrong_provenance["provenance"]["model"] = candidate_model
        write(admission_path, wrong_provenance)
        invalid_cache = copy.deepcopy(cache)
        invalid_cache["admission"]["score_proof"] = proof(
            admission_path, "clawgauge-local-cache-admission-score"
        )
        blockers = []
        assert compare.validate_local_admission(
            blockers, "baseline", route_prov, invalid_cache, root
        )["valid"] is False
        assert any("provenance differs" in item for item in blockers)
        checks += 2

    print(f"ClawGauge decision-grade tests: PASS ({checks} assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
