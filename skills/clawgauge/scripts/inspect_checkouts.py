#!/usr/bin/env python3
"""Record local benchmark checkout provenance without fetching or changing it."""

from __future__ import annotations

import argparse
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from typing import Any


def display_path(path: Path) -> str:
    home = Path.home().resolve()
    try:
        return "$HOME/" + str(path.resolve().relative_to(home))
    except ValueError:
        return path.name


def git(repo: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(
            ["git", *args],
            cwd=repo,
            text=True,
            capture_output=True,
            check=True,
            timeout=20,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    return result.stdout.strip()


def package_version(repo: Path) -> str | None:
    package = repo / "package.json"
    if not package.is_file():
        return None
    try:
        data = json.loads(package.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    value = data.get("version") if isinstance(data, dict) else None
    return str(value) if value else None


def inspect(label: str, repo: Path) -> dict[str, Any]:
    resolved = repo.expanduser().resolve()
    result: dict[str, Any] = {
        "label": label,
        "path": display_path(resolved),
        "exists": resolved.is_dir(),
        "git_checkout": False,
    }
    if not resolved.is_dir():
        result["blocker"] = "checkout missing"
        return result
    head = git(resolved, "rev-parse", "HEAD")
    if not head:
        result["blocker"] = "not a readable git checkout"
        return result
    result.update(
        {
            "git_checkout": True,
            "head": head,
            "branch": git(resolved, "branch", "--show-current") or "detached",
            "package_version": package_version(resolved),
        }
    )
    status = git(resolved, "status", "--porcelain=v1", "--untracked-files=normal")
    lines = status.splitlines() if status else []
    result["dirty"] = bool(lines)
    result["dirty_entry_count"] = len(lines)
    result["upstream"] = git(resolved, "rev-parse", "--abbrev-ref", "@{upstream}")
    if result["upstream"]:
        divergence = git(
            resolved,
            "rev-list",
            "--left-right",
            "--count",
            f"HEAD...{result['upstream']}",
        )
        if divergence:
            try:
                ahead, behind = (int(part) for part in divergence.split())
                result["ahead"] = ahead
                result["behind"] = behind
            except (TypeError, ValueError):
                result["divergence"] = "unavailable"
    else:
        result["divergence"] = "no tracking branch"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--openclaw",
        type=Path,
        default=Path(os.environ.get("CLAWGAUGE_OPENCLAW_ROOT", "~/projects/openclaw")),
    )
    parser.add_argument(
        "--shellbench",
        type=Path,
        default=Path(os.environ.get("CLAWGAUGE_SHELLBENCH_ROOT", "~/projects/shellbench")),
    )
    parser.add_argument("--out", type=Path)
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit 2 when a checkout is missing, dirty, or behind its known tracking branch",
    )
    args = parser.parse_args()
    report = {
        "schema_version": "clawgauge.checkout-audit.v1",
        "host": {
            "os": platform.system().lower(),
            "architecture": platform.machine().lower(),
        },
        "network_refresh_performed": False,
        "checkouts": [
            inspect("openclaw", args.openclaw),
            inspect("shellbench", args.shellbench),
        ],
    }
    rendered = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(rendered, encoding="utf-8")
    else:
        sys.stdout.write(rendered)
    if args.strict and any(
        item.get("blocker") or item.get("dirty") or int(item.get("behind") or 0) > 0
        for item in report["checkouts"]
    ):
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
