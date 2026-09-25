#!/usr/bin/env python3
"""Analyze requested-route scores while keeping effective-route proof explicit."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import json
import math
import statistics
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

RUNNER = Path(__file__).with_name("run_personal_campaign.py")
spec = importlib.util.spec_from_file_location("personal_runner", RUNNER)
runner = importlib.util.module_from_spec(spec)
assert spec.loader
spec.loader.exec_module(runner)


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def file_sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def one_score(result: dict[str, Any], task: str) -> tuple[float, dict[str, Any]]:
    rows = [row for row in result.get("task_results", []) if row.get("task_id") == task]
    if len(rows) != 1:
        raise ValueError("native result must contain exactly one TaskStats row for the scheduled task")
    row = rows[0]
    score = row.get("mean_run_score")
    scores = row.get("scores")
    if row.get("runs") != 1 or type(score) not in (int, float):
        raise ValueError("native TaskStats must contain one run and a numeric mean_run_score")
    if not isinstance(scores, list) or len(scores) != 1 or type(scores[0]) not in (int, float):
        raise ValueError("native TaskStats.scores must bind the single aggregate run")
    score = float(score)
    raw_score = float(scores[0])
    if not math.isfinite(score) or not math.isfinite(raw_score):
        raise ValueError("native score must be finite")
    if not 0.0 <= score <= 1.0 or not math.isclose(score, raw_score, abs_tol=1e-9):
        raise ValueError("native aggregate score is invalid or inconsistent")
    return score, row


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-dir", type=Path, required=True)
    parser.add_argument("--out", type=Path, required=True)
    parser.add_argument("--json", dest="json_out", type=Path, required=True)
    args = parser.parse_args()

    manifest = json.loads((args.run_dir / "manifest.json").read_text())
    schedule = json.loads((args.run_dir / "schedule.json").read_text())
    runner.verify_frozen(manifest, args.run_dir, schedule)

    blockers: list[str] = []
    proof_gaps: list[str] = []
    failures: Counter[str] = Counter()
    scores: dict[str, dict[str, list[float]]] = defaultdict(lambda: defaultdict(list))
    usage_rows: list[dict[str, Any]] = []
    scored = 0
    verified = 0
    if (args.run_dir / "execution-blocked.json").exists():
        blockers.extend(json.loads((args.run_dir / "execution-blocked.json").read_text())["execution_blockers"])

    frozen = json.loads((args.run_dir / "freeze.json").read_text())
    task_fingerprints = {item["id"]: item["sha256"] for item in frozen["tasks"]}
    infra_failure_modes = {"environment_unavailable", "timeout"}

    for cell in schedule:
        prefix = f"{cell['sequence']:02d}-{cell['route']}-{cell['task']}-r{cell['repetition']}"
        cell_root = args.run_dir / "cells" / prefix
        spec_path = cell_root / "cell.json"
        supervisor_path = cell_root / "supervisor-receipt.json"
        worker_path = cell_root / "worker-receipt.json"
        native_path = cell_root / "native-result.json"
        if not spec_path.exists() or not supervisor_path.exists():
            failures["missing"] += 1
            continue
        spec = json.loads(spec_path.read_text())
        supervisor = json.loads(supervisor_path.read_text())
        expected_contract = runner.cell_contract(
            manifest, cell, task_fingerprints[cell["task"]]
        )
        expected_digest = runner.digest(expected_contract)
        if (
            spec.get("cell_contract") != expected_contract
            or spec.get("cell_sha256") != expected_digest
            or supervisor.get("cell_sha256") != expected_digest
        ):
            blockers.append(f"{prefix}: supervisor/cell identity binding mismatch")
            continue
        if supervisor.get("retry") != 0:
            blockers.append(f"{prefix}: retry metadata violates frozen protocol")
        if supervisor.get("exit_code") != 0:
            failures["infra_timeout" if supervisor.get("timed_out") else "infra_failure"] += 1
            continue
        if not worker_path.exists() or not native_path.exists():
            failures["missing"] += 1
            continue
        receipt = json.loads(worker_path.read_text())
        try:
            bound_native = Path(receipt.get("native_result", "")).resolve()
        except (TypeError, OSError):
            bound_native = Path()
        if (
            receipt.get("cell_sha256") != expected_digest
            or receipt.get("task_fingerprint") != task_fingerprints[cell["task"]]
            or bound_native != native_path.resolve()
            or receipt.get("native_result_sha256") != file_sha256(native_path)
        ):
            blockers.append(f"{prefix}: worker/native result binding mismatch")
            continue
        native = json.loads(native_path.read_text())
        requested = runner.route_for(manifest, cell["route"])
        if any(native.get(key) != requested[key] for key in ("model", "provider")):
            blockers.append(f"{prefix}: native requested-route label mismatch")
            continue
        if receipt.get("effective_route_proof") == "verified":
            blockers.append(f"{prefix}: unsupported self-declared effective route proof")
            continue
        try:
            score, task_row = one_score(native, cell["task"])
        except ValueError as exc:
            blockers.append(f"{prefix}: {exc}")
            continue
        failure_counts = task_row.get("failure_mode_counts", {})
        if not isinstance(failure_counts, dict) or any(
            not isinstance(count, int) or count < 0 for count in failure_counts.values()
        ):
            blockers.append(f"{prefix}: invalid aggregate failure_mode_counts")
            continue
        for mode, count in failure_counts.items():
            category = "scored_infra_failure" if mode in infra_failure_modes else "quality_failure"
            failures[category] += count
        scores[cell["route"]][cell["task"]].append(score)
        scored += 1
        usage_rows.append(receipt.get("usage", {}))
        if receipt.get("effective_route_proof") == "verified":
            verified += 1
        else:
            missing = receipt.get("missing_effective_route_proof", [])
            proof_gaps.append(f"{prefix}: missing independent proof for {', '.join(missing)}")
            if receipt.get("evidence_tier") == "strict-decision-grade":
                blockers.append(f"{prefix}: strict decision-grade effective-route proof unavailable")

    if scored != len(schedule):
        blockers.append(f"scored cells incomplete: {scored}/{len(schedule)}")
    summary: dict[str, Any] = {}
    for route_id, tasks in scores.items():
        task_summary = {}
        all_scores: list[float] = []
        for task_id, values in tasks.items():
            task_summary[task_id] = {
                "n": len(values),
                "mean_score": statistics.mean(values),
                "worst_of_n": min(values),
                "scores": values,
            }
            all_scores.extend(values)
        summary[route_id] = {
            "n": len(all_scores),
            "mean_score": statistics.mean(all_scores) if all_scores else None,
            "worst_of_n": min(all_scores) if all_scores else None,
            "tasks": task_summary,
        }

    usage_fields = (
        "input_tokens", "output_tokens", "reasoning_tokens", "cache_read_tokens",
        "cache_write_tokens", "total_tokens", "cost_usd",
    )
    usage_totals: dict[str, int | float | None] = {}
    for field in usage_fields:
        values = [row.get(field) for row in usage_rows]
        usage_totals[field] = sum(values) if len(values) == len(schedule) and all(isinstance(v, (int, float)) for v in values) else None
    estimated_values = [row.get("estimated_cost_usd") for row in usage_rows]
    native_estimated_cost = (
        sum(estimated_values) if len(estimated_values) == len(schedule)
        and all(isinstance(value, (int, float)) for value in estimated_values) else None
    )
    if not usage_rows or all(row.get("status") == "n/a" for row in usage_rows):
        usage_status = "n/a"
    elif len(usage_rows) == len(schedule) and all(row.get("status") == "observed" for row in usage_rows):
        usage_status = "observed"
    else:
        usage_status = "partial"

    if failures["scored_infra_failure"]:
        blockers.append("native infrastructure failures prevent a capability conclusion")
    complete = scored == len(schedule) and not blockers
    result = {
        "schema": "clawgauge.personal-comparison.v5",
        "verdict": "requested-route-screening-complete" if complete else "blocked",
        "confidence": "directional-requested-route" if complete else "unavailable",
        "claim_scope": "requested routes only; effective route identity remains unproven",
        "decision_grade": False,
        "complete_frozen_matrix": complete,
        "scored_cells": scored,
        "effective_route_verified_cells": verified,
        "expected_cells": len(schedule),
        "score_summary": summary,
        "blockers": sorted(set(blockers)),
        "effective_route_proof_gaps": proof_gaps,
        "failure_categories": dict(failures),
        "usage_status": usage_status,
        "actual_usage": usage_totals,
        "native_estimated_cost_usd": native_estimated_cost,
        "soft_estimated_usd": manifest.get("soft_accounting", {}).get("estimated_usd"),
        "hard_dollar_gate": False,
    }
    write_json(args.json_out, result)
    lines = [
        "# ClawGauge Personal Comparison", "",
        f"- Verdict: **{result['verdict']}**",
        f"- Confidence: {result['confidence']}",
        f"- Scored cells: {scored}/{len(schedule)}",
        f"- Effective-route verified cells: {verified}/{len(schedule)}",
        "- Decision-grade: no",
        f"- Usage: {usage_status}; missing fields remain null",
        "", "## Score scope", "",
        "Scores describe the requested routes only. They are not proof of the effective",
        "provider/model, account, reasoning, fast state, or fallback behavior.",
        "", "## Route summaries", "",
    ]
    for route_id, route_summary in sorted(summary.items()):
        lines.append(f"- {route_id}: n={route_summary['n']}, mean={route_summary['mean_score']:.3f}, worst={route_summary['worst_of_n']:.3f}")
    if result["blockers"]:
        lines.extend(["", "## Blockers", ""] + [f"- {item}" for item in result["blockers"]])
    if proof_gaps:
        lines.extend(["", "## Missing effective-route proof", ""] + [f"- {item}" for item in proof_gaps])
    if failures:
        lines.extend(["", "## Failure categories", ""] + [f"- {name}: {count}" for name, count in sorted(failures.items())])
    args.out.write_text("\n".join(lines) + "\n")
    return 2 if blockers else 0


if __name__ == "__main__":
    raise SystemExit(main())
