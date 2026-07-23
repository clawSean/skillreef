#!/usr/bin/env python3
"""Summarize a ClawBench result JSON into a compact Markdown report.

Usage:
  python scripts/summarize_clawbench_result.py results/model-smoke.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from statistics import mean
from typing import Any


def get(data: dict[str, Any], *keys: str, default: Any = None) -> Any:
    cur: Any = data
    for key in keys:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur


def task_stats(data: dict[str, Any]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    for tier in data.get("tier_results", []) or []:
        for task in tier.get("task_stats", []) or []:
            if isinstance(task, dict):
                out.append(task)
    if out:
        return out
    for key in ("task_stats", "tasks"):
        raw = data.get(key)
        if isinstance(raw, list):
            return [x for x in raw if isinstance(x, dict)]
    return []


def fmt_num(value: Any, digits: int = 3) -> str:
    try:
        return f"{float(value):.{digits}f}"
    except Exception:
        return "n/a"


def main() -> int:
    if len(sys.argv) != 2:
        print("usage: summarize_clawbench_result.py <result.json>", file=sys.stderr)
        return 2
    path = Path(sys.argv[1])
    data = json.loads(path.read_text(encoding="utf-8"))
    tasks = task_stats(data)

    scores = []
    pass_rates = []
    worst = []
    for task in tasks:
        for key in ("mean_task_score", "task_score", "mean_run_score", "mean"):
            if key in task:
                try:
                    scores.append(float(task[key]))
                except Exception:
                    pass
                break
        if "pass_rate" in task:
            try:
                pass_rates.append(float(task["pass_rate"]))
            except Exception:
                pass
        for key in ("worst_of_n", "min_score"):
            if key in task:
                try:
                    worst.append(float(task[key]))
                except Exception:
                    pass
                break

    model = data.get("model") or get(data, "metadata", "model", default="unknown")
    overall = data.get("overall_score")
    if overall is None and scores:
        overall = mean(scores)

    print(f"# ClawBench Summary: {model}")
    print()
    print(f"- Source: `{path}`")
    print(f"- Overall score: {fmt_num(overall)}")
    print(f"- Tasks summarized: {len(tasks)}")
    if pass_rates:
        print(f"- Mean pass rate: {fmt_num(mean(pass_rates))}")
    if worst:
        print(f"- Worst-of-n mean: {fmt_num(mean(worst))}")
    for key, label in (
        ("overall_cost_per_pass", "Cost/pass"),
        ("overall_tokens_per_pass", "Tokens/pass"),
        ("total_estimated_cost_usd", "Total estimated cost"),
        ("total_tokens", "Total tokens"),
    ):
        if key in data:
            print(f"- {label}: {data[key]}")
    print()
    if tasks:
        print("## Tasks")
        for task in tasks:
            tid = task.get("task_id") or task.get("id") or "unknown-task"
            score = None
            for key in ("mean_task_score", "task_score", "mean_run_score", "mean"):
                if key in task:
                    score = task[key]
                    break
            bits = [f"score={fmt_num(score)}"]
            if "pass_rate" in task:
                bits.append(f"pass_rate={fmt_num(task['pass_rate'])}")
            if "pass_hat_k" in task:
                bits.append(f"pass^k={task['pass_hat_k']}")
            if "worst_of_n" in task:
                bits.append(f"worst={fmt_num(task['worst_of_n'])}")
            print(f"- `{tid}`: " + ", ".join(bits))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
