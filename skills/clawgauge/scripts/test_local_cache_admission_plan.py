#!/usr/bin/env python3
"""Provider-free tests for local cache admission planning."""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
BUILDER = ROOT / "scripts" / "build_local_cache_admission_plan.py"
HASH = "sha256:" + "a" * 64


def base(runtime: str, version: str) -> list[str]:
    return [
        "--runtime", runtime, "--runtime-version", version,
        "--model", "exact-model", "--model-revision", "abcdef1234567",
        "--openclaw-commit", "1234567abcdef",
        "--cache-layout-fingerprint", HASH,
    ]


def run(root: Path, label: str, expected: int, args: list[str]) -> dict:
    out = root / f"{label}.json"
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


def main() -> int:
    checks = 0
    with tempfile.TemporaryDirectory(prefix="clawgauge-cache-admission-") as raw:
        root = Path(raw)
        old = run(root, "old", 2, base("mlx-vlm", "0.6.13"))
        assert not old["ok_to_execute"]
        assert any("0.6.14" in item for item in old["blockers"])
        checks += 2

        hybrid = run(
            root, "hybrid", 0,
            base("mlx-vlm", "0.6.14")
            + ["--feature", "hybrid-recurrent", "--feature", "multimodal"],
        )
        ids = {case["id"] for case in hybrid["cases"]}
        assert hybrid["network_calls_performed"] == 0
        assert "stateful-branch-replay" in ids
        assert "media-key-isolation" in ids
        assert hybrid["claim_if_all_pass"] == "cache-qualified"
        assert "promoted" in hybrid["claim_not_granted"]
        checks += 5

        lm = run(
            root, "lm", 0,
            base("mlx-lm", "0.31.3") + ["--feature", "shared-service"],
        )
        ids = {case["id"] for case in lm["cases"]}
        assert "tenant-and-eviction-isolation" in ids
        assert any("not a universal hard cap" in item for item in lm["warnings"])
        checks += 2

    print(f"ClawGauge local cache admission tests: PASS ({checks} assertions)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
