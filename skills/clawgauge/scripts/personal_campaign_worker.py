#!/usr/bin/env python3
"""Execute one isolated ShellBench cell without touching production OpenClaw state."""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import json
import os
import re
import socket
import subprocess
import sys
import time
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from personal_campaign_config import validate_prepared_config
from process_cleanup import terminate_process_tree

PRODUCTION_PORT = 18789
PRODUCTION_TOKEN_ENV_DENYLIST = frozenset(
    {
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "XAI_API_KEY",
        "GEMINI_API_KEY",
        "GOOGLE_API_KEY",
        "OPENROUTER_API_KEY",
        "AWS_ACCESS_KEY_ID",
        "AWS_SECRET_ACCESS_KEY",
        "AZURE_OPENAI_API_KEY",
        "OPENCLAW_GATEWAY_TOKEN",
        "OPENCLAW_GATEWAY_PASSWORD",
        "OPENCLAW_AUTH_TOKEN",
    }
)
REQUIRED_CONTROLS = frozenset(
    {"auth_account", "effective_provider_model", "fallback", "fast", "reasoning"}
)


def canonical_path(value: str | Path) -> Path:
    return Path(value).expanduser().resolve()


def lexical_path(value: str | Path) -> Path:
    return Path(os.path.abspath(os.path.expanduser(str(value))))


def require_realpath(name: str, value: str | Path) -> Path:
    lexical = lexical_path(value)
    resolved = canonical_path(value)
    if lexical != resolved:
        raise ValueError(f"{name} contains a symlinked path component")
    return resolved


def is_within(path: Path, root: Path) -> bool:
    try:
        path.relative_to(root)
        return True
    except ValueError:
        return False


def collides(path: Path, protected: Path) -> bool:
    return path == protected or is_within(path, protected) or is_within(protected, path)


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def object_sha256(value: Any) -> str:
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(payload).hexdigest()


def parse_endpoint(url: str) -> tuple[str, int]:
    parsed = urlparse(url)
    if (
        parsed.scheme != "ws"
        or parsed.hostname != "127.0.0.1"
        or parsed.username
        or parsed.password
        or parsed.path not in ("", "/")
        or parsed.params
        or parsed.query
        or parsed.fragment
        or parsed.port is None
    ):
        raise ValueError("gateway_url must be an explicit ws://127.0.0.1:<port> endpoint")
    if parsed.port == PRODUCTION_PORT:
        raise ValueError("production Gateway port 18789 is forbidden")
    return parsed.hostname, parsed.port


def validate_spec(spec: dict[str, Any]) -> dict[str, Any]:
    run_root = require_realpath("run_root", spec["run_root"])
    runtime_root = require_realpath("runtime_root", spec["runtime_root"])
    cell_root = require_realpath("cell_root", spec["cell_root"])
    evidence_root = require_realpath("evidence_root", spec["evidence_root"])
    if not is_within(cell_root, runtime_root) or cell_root == runtime_root:
        raise ValueError("cell_root must be a distinct child of runtime_root")
    if not is_within(evidence_root, run_root) or evidence_root == run_root:
        raise ValueError("evidence_root must be a distinct child of run_root")

    roots = {
        name: require_realpath(name, spec[name])
        for name in ("home", "state_dir", "config_path", "workspace_root")
    }
    output_path = require_realpath("output_path", spec["output_path"])
    for name, path in roots.items():
        if not is_within(path, cell_root):
            raise ValueError(f"{name} must stay inside cell_root")
    if not is_within(output_path, evidence_root):
        raise ValueError("output_path must stay inside evidence_root")
    expected_workspace = roots["state_dir"] / "workspace-clawbench"
    if roots["workspace_root"] != expected_workspace:
        raise ValueError("workspace_root must be the ShellBench workspace root inside state_dir")

    production = canonical_path(Path.home() / ".openclaw")
    protected = [
        production / "openclaw.json",
        production / "auth-profiles.json",
        production / "agents",
        production / "credentials",
        production / "identity",
        production / "sessions",
    ]
    for name, path in {**roots, "runtime_root": runtime_root, "cell_root": cell_root}.items():
        if any(collides(path, target) for target in protected):
            raise ValueError(f"{name} collides with a production config/auth/agent runtime tree")

    host, port = parse_endpoint(str(spec["gateway_url"]))
    command = spec.get("gateway_command")
    if not isinstance(command, list) or len(command) < 3 or not all(isinstance(v, str) for v in command):
        raise ValueError("gateway_command must be a non-empty argv list")
    if Path(command[0]).name != "openclaw" or command[1:3] != ["gateway", "run"]:
        raise ValueError("gateway_command must invoke 'openclaw gateway run'")
    if "--profile" in command or "--force" in command:
        raise ValueError("diagnostic/profile and force flags are forbidden")
    if "--bind" not in command or command[command.index("--bind") + 1] != "loopback":
        raise ValueError("Gateway must bind loopback")
    if "--port" not in command or int(command[command.index("--port") + 1]) != port:
        raise ValueError("Gateway command port must match gateway_url")
    if spec.get("adapter") != "openclaw":
        raise ValueError("only the pinned executable openclaw adapter is supported")
    if not re.fullmatch(r"[0-9a-f]{64}", str(spec.get("task_fingerprint", ""))):
        raise ValueError("task_fingerprint must be a SHA-256 digest")
    if spec.get("cell_sha256") != object_sha256(spec.get("cell_contract")):
        raise ValueError("cell identity digest mismatch")

    preparation = spec.get("auth_preparation", {})
    if preparation.get("kind") not in {
        "provider-free-mock",
        "isolated-api-config",
        "subscription-handoff",
    }:
        raise ValueError("unsupported auth preparation")
    if preparation["kind"] == "subscription-handoff":
        raise RuntimeError("exact subscription handoff into the disposable Gateway is unsupported")
    if preparation.get("config_sha256") != sha256(roots["config_path"]):
        raise ValueError("prepared config SHA-256 does not match copied config")
    config_text = roots["config_path"].read_text(errors="replace")
    validate_prepared_config(config_text, spec)
    endpoint = str(preparation.get("provider_endpoint", ""))
    if endpoint not in config_text:
        raise ValueError("explicit provider endpoint is absent from copied config")
    if preparation["kind"] == "provider-free-mock" and not endpoint.startswith("http://127.0.0.1:"):
        raise ValueError("provider-free mock endpoint must be loopback")
    if preparation["kind"] == "isolated-api-config":
        if preparation.get("credential_env") != "CLAWGAUGE_ISOLATED_API_KEY":
            raise ValueError("isolated API config must use CLAWGAUGE_ISOLATED_API_KEY")
        if not os.environ.get("CLAWGAUGE_ISOLATED_API_KEY"):
            raise RuntimeError("CLAWGAUGE_ISOLATED_API_KEY is not prepared")

    required = set(spec.get("required_observed_controls", []))
    if required != REQUIRED_CONTROLS:
        raise ValueError("all effective-route proof requirements must remain frozen")
    observed = set(spec.get("independently_observed_controls", []))
    if not observed.issubset(REQUIRED_CONTROLS):
        raise ValueError("unknown independently observed control")
    if observed:
        raise ValueError("independently observed controls cannot be self-declared")
    if spec.get("evidence_tier") == "strict-decision-grade" and required - observed:
        raise RuntimeError(
            "strict decision-grade proof missing: " + ", ".join(sorted(required - observed))
        )
    if spec.get("evidence_tier") not in {"requested-route-screening", "strict-decision-grade"}:
        raise ValueError("unsupported evidence tier")

    return {
        "run_root": run_root,
        "runtime_root": runtime_root,
        "cell_root": cell_root,
        "evidence_root": evidence_root,
        "host": host,
        "port": port,
        "output_path": output_path,
        **roots,
    }


def assert_no_production_tokens() -> None:
    present = sorted(name for name in PRODUCTION_TOKEN_ENV_DENYLIST if os.environ.get(name))
    if present:
        raise RuntimeError("production credential environment is forbidden: " + ", ".join(present))


def isolated_env(paths: dict[str, Any], spec: dict[str, Any]) -> dict[str, str]:
    env = {
        "PATH": os.environ.get("PATH", os.defpath),
        "LANG": os.environ.get("LANG", "C.UTF-8"),
        "HOME": str(paths["home"]),
        "OPENCLAW_HOME": str(paths["home"]),
        "OPENCLAW_STATE_DIR": str(paths["state_dir"]),
        "OPENCLAW_CONFIG_PATH": str(paths["config_path"]),
        "CLAWBENCH_RUN_CACHE_DIR": "",
        "CLAWBENCH_KEEP_WORKSPACES": "1",
        "CLAWBENCH_PER_RUN_BUDGET_SECONDS": "150",
        "CLAWBENCH_PER_TURN_TIMEOUT_SECONDS": "120",
    }
    credential_env = spec["auth_preparation"].get("credential_env")
    if credential_env:
        env[credential_env] = os.environ[credential_env]
    return env


def listener_open(host: str, port: int) -> bool:
    with socket.socket() as sock:
        sock.settimeout(0.1)
        return sock.connect_ex((host, port)) == 0


def wait_for_listener(host: str, port: int, process: subprocess.Popen[str], timeout: float) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"isolated Gateway exited before readiness: {process.returncode}")
        if listener_open(host, port):
            return
        time.sleep(0.05)
    raise TimeoutError("isolated Gateway readiness deadline exceeded")


def stop_process_group(process: subprocess.Popen[str], grace: float = 10.0) -> None:
    terminate_process_tree(process, grace)


def wait_for_listener_closed(host: str, port: int, timeout: float = 2.0) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if not listener_open(host, port):
            return
        time.sleep(0.05)
    raise RuntimeError("isolated Gateway listener remained open after process-group cleanup")


async def run_harness(spec: dict[str, Any]) -> tuple[dict[str, Any], str]:
    memo_env = os.environ.get("CLAWBENCH_RUN_CACHE_DIR")
    if memo_env != "":
        raise RuntimeError("CLAWBENCH_RUN_CACHE_DIR must be observed empty at harness entry")
    from clawbench.client import GatewayConfig
    from clawbench.harness import BenchmarkHarness

    harness = BenchmarkHarness(
        gateway_config=GatewayConfig(url=spec["gateway_url"], token=""),
        model=spec["model"],
        provider=spec["provider"],
        adapter=spec["adapter"],
        task_ids=[spec["task"]],
        runs_per_task=1,
        concurrency=1,
        randomize_order=False,
        judge_model="",
        judge_affects_score=False,
        print_report=False,
        quiet=True,
    )
    result = await harness.run()
    return result.model_dump(mode="json"), memo_env


def usage_summary(result: dict[str, Any]) -> dict[str, Any]:
    """Report only nonzero native usage; serialized zero defaults have no provenance."""
    mapping = {
        "input_tokens": "overall_input_tokens",
        "output_tokens": "overall_output_tokens",
        "reasoning_tokens": "overall_reasoning_tokens",
        "total_tokens": "overall_total_tokens",
    }
    totals: dict[str, int | float | None] = {
        "input_tokens": None,
        "output_tokens": None,
        "reasoning_tokens": None,
        "cache_read_tokens": None,
        "cache_write_tokens": None,
        "total_tokens": None,
        "cost_usd": None,
        "estimated_cost_usd": None,
    }
    observed_fields: list[str] = []
    for target, source in mapping.items():
        value = result.get(source)
        if isinstance(value, (int, float)) and value > 0:
            totals[target] = int(value)
            observed_fields.append(target)
    estimated_cost = result.get("overall_cost_usd")
    if isinstance(estimated_cost, (int, float)) and estimated_cost > 0:
        totals["estimated_cost_usd"] = float(estimated_cost)
    return {
        "status": "partial" if observed_fields else "n/a",
        "provenance": "native-nonzero-aggregate" if observed_fields else "unavailable",
        "observed_fields": observed_fields,
        "cost_basis": "estimate-not-billed-actual" if totals["estimated_cost_usd"] is not None else "n/a",
        **totals,
    }


def write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")
    os.chmod(path, 0o600)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cell", type=Path, required=True)
    args = parser.parse_args()
    spec = json.loads(args.cell.read_text())
    try:
        assert_no_production_tokens()
        paths = validate_spec(spec)
        if listener_open(paths["host"], paths["port"]):
            raise RuntimeError("isolated Gateway endpoint is already occupied")
    except (KeyError, TypeError, ValueError, RuntimeError) as exc:
        print(f"BLOCKED before Gateway/provider contact: {exc}", file=sys.stderr)
        return 78

    for name in ("home", "state_dir"):
        paths[name].mkdir(parents=True, exist_ok=False)
    if not paths["config_path"].is_file():
        print("BLOCKED before Gateway/provider contact: run-local config_path is missing", file=sys.stderr)
        return 78

    env = isolated_env(paths, spec)
    os.environ.clear()
    os.environ.update(env)
    started = time.monotonic()
    gateway_log = paths["evidence_root"] / "gateway.log"
    gateway: subprocess.Popen[str] | None = None
    cleanup_error: str | None = None
    try:
        with gateway_log.open("w", encoding="utf-8") as log:
            gateway = subprocess.Popen(
                spec["gateway_command"],
                cwd=paths["cell_root"],
                env=env,
                stdout=log,
                stderr=subprocess.STDOUT,
                text=True,
                start_new_session=True,
            )
            wait_for_listener(paths["host"], paths["port"], gateway, spec.get("readiness_seconds", 30))
            result, memo_env = asyncio.run(run_harness(spec))
        write_json(paths["output_path"], result)
        native_result_sha256 = sha256(paths["output_path"])
        required = set(spec["required_observed_controls"])
        observed = set(spec.get("independently_observed_controls", []))
        missing = sorted(required - observed)
        write_json(
            paths["evidence_root"] / "worker-receipt.json",
            {
                "schema": "clawgauge.personal-cell-receipt.v2",
                "duration_seconds": round(time.monotonic() - started, 3),
                "fresh_workspace_root": str(paths["workspace_root"]),
                "memo_cache": "disabled",
                "memo_env_at_harness_entry": memo_env,
                "task_fingerprint": spec["task_fingerprint"],
                "cell_sha256": spec["cell_sha256"],
                "native_result": str(paths["output_path"]),
                "native_result_sha256": native_result_sha256,
                "requested_route": {
                    "provider": spec["provider"],
                    "model": spec["model"],
                    "adapter": spec["adapter"],
                },
                "evidence_tier": spec["evidence_tier"],
                "effective_route_proof": "verified" if not missing else "unavailable",
                "missing_effective_route_proof": missing,
                "claim_scope": "requested-route-screening" if missing else "strict-decision-grade",
                "usage": usage_summary(result),
            },
        )
        return 0
    finally:
        if gateway is not None:
            stop_process_group(gateway)
            try:
                wait_for_listener_closed(paths["host"], paths["port"])
            except RuntimeError as exc:
                cleanup_error = str(exc)
        if cleanup_error:
            write_json(paths["evidence_root"] / "cleanup-failure.json", {"error": cleanup_error})
            print(cleanup_error, file=sys.stderr)
            return 70


if __name__ == "__main__":
    raise SystemExit(main())
