#!/usr/bin/env python3
"""Provider-free regressions for executable personal campaign isolation."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import shutil
import signal
import socket
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SHELLBENCH_ROOT = Path(
    os.environ.get("CLAWGAUGE_SHELLBENCH_ROOT", Path.home() / "projects" / "shellbench")
).expanduser().resolve()
SHELLBENCH_PYTHON = Path(os.environ.get("CLAWGAUGE_SHELLBENCH_PYTHON", SHELLBENCH_ROOT / ".venv" / "bin" / "python")).expanduser().resolve()
CAMPAIGN_PYTHON = Path(
    os.environ.get("CLAWGAUGE_TEST_PYTHON")
    or shutil.which("python3.13")
    or shutil.which("python3.12")
    or shutil.which("python3.11")
    or (str(SHELLBENCH_PYTHON) if SHELLBENCH_PYTHON.is_file() else sys.executable)
).expanduser().resolve()


def load(name: str, path: Path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader
    spec.loader.exec_module(module)
    return module


campaign = load("campaign", ROOT / "run_personal_campaign.py")
worker = load("worker", ROOT / "personal_campaign_worker.py")
analyzer = load("analyzer", ROOT / "analyze_personal_campaign.py")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def route(route_id: str, config_hash: str, provider_endpoint: str) -> dict:
    return {
        "id": route_id,
        "provider": "mock",
        "model": f"mock/{route_id}",
        "adapter": "openclaw",
        "reasoning": "requested-high",
        "fast": False,
        "fallback": False,
        "tools_profile": "default",
        "auth_account": f"mock-{route_id}",
        "evidence_tier": "requested-route-screening",
        "required_observed_controls": list(campaign.REQUIRED_CONTROLS),
        "independently_observed_controls": [],
        "auth_preparation": {
            "kind": "provider-free-mock",
            "provider_endpoint": provider_endpoint,
            "credential_env": None,
            "config_sha256": config_hash,
        },
    }


def manifest(config_path: Path, gateway_port: int, provider_endpoint: str) -> dict:
    config_hash = digest(config_path)
    return {
        "schema": campaign.SCHEMA,
        "campaign_id": "provider-free",
        "routes": [route("a", config_hash, provider_endpoint), route("b", config_hash, provider_endpoint)],
        "repetitions": 3,
        "tasks": list(campaign.TASKS),
        "automatic_retries": 0,
        "shellbench": {
            "root": str(SHELLBENCH_ROOT),
            "commit": "884dd1bb55112c93292e1633081d62504ba49905",
            "python": str(SHELLBENCH_PYTHON),
        },
        "gateway": {
            "url": f"ws://127.0.0.1:{gateway_port}",
            "executable": "/tmp/openclaw",
            "config_source": str(config_path),
            "token_env": "",
        },
        "bounds": {
            "cell_timeout_seconds": 180,
            "campaign_timeout_seconds": 4200,
            "kill_grace_seconds": 2,
        },
        "soft_accounting": {"estimated_usd": None, "warning_minutes": 45},
    }


def production_snapshot():
    config = Path.home() / ".openclaw" / "openclaw.json"
    agents = Path.home() / ".openclaw" / "agents"
    config_state = None
    if config.is_file():
        stat = config.stat()
        config_state = (stat.st_mtime_ns, stat.st_size, digest(config))
    roster = sorted(path.name for path in agents.iterdir() if path.is_dir()) if agents.is_dir() else []
    return config_state, roster


def write_fake_stack(root: Path) -> tuple[Path, Path]:
    package = root / "fake-python" / "clawbench"
    package.mkdir(parents=True)
    (package / "__init__.py").write_text("")
    (package / "client.py").write_text(
        "class GatewayConfig:\n"
        "    def __init__(self, **kwargs): self.__dict__.update(kwargs)\n"
    )
    (package / "harness.py").write_text(
        "import json, os, socket, time, uuid\n"
        "from pathlib import Path\n"
        "from urllib.parse import urlparse\n"
        "class Result:\n"
        "    def __init__(self, task, model, provider): self.task, self.model, self.provider = task, model, provider\n"
        "    def model_dump(self, **kwargs):\n"
        "        return {'model': self.model, 'provider': self.provider, 'overall_input_tokens': 0, 'overall_output_tokens': 7, "
        "'overall_reasoning_tokens': 0, 'overall_total_tokens': 0, 'overall_cost_usd': 0, "
        "'task_results': [{'task_id': self.task, 'runs': 1, 'mean_run_score': 0.75, "
        "'scores': [0.75], 'failure_mode_counts': {}}]}\n"
        "class BenchmarkHarness:\n"
        "    def __init__(self, **kwargs): self.kwargs = kwargs\n"
        "    async def run(self):\n"
        "        ports = [urlparse(self.kwargs['gateway_config'].url).port]\n"
        "        cfg = json.loads(Path(os.environ['OPENCLAW_CONFIG_PATH']).read_text())\n"
        "        ports.append(urlparse(cfg['mock_provider_endpoint']).port)\n"
        "        time.sleep(float(cfg.get('sleep_seconds', 0)))\n"
        "        if cfg.get('fail_model') == self.kwargs['model'] and cfg.get('fail_task') == self.kwargs['task_ids'][0]: raise RuntimeError('synthetic partial failure')\n"
        "        for index, port in enumerate(ports):\n"
        "            deadline = time.monotonic() + 2\n"
        "            while True:\n"
        "                try:\n"
        "                    with socket.create_connection(('127.0.0.1', port), timeout=.2) as conn:\n"
        "                        if index == 0: conn.sendall(b'agents.create\\n')\n"
        "                    break\n"
        "                except OSError:\n"
        "                    if time.monotonic() >= deadline: raise\n"
        "                    time.sleep(.02)\n"
        "        workspace = Path(os.environ['OPENCLAW_STATE_DIR']) / 'workspace-clawbench' / uuid.uuid4().hex\n"
        "        workspace.mkdir(parents=True)\n"
        "        (workspace / 'executed').write_text('fresh')\n"
        "        return Result(self.kwargs['task_ids'][0], self.kwargs['model'], self.kwargs['provider'])\n"
    )
    executable = root / "bin" / "openclaw"
    executable.parent.mkdir()
    executable.write_text(
        "#!/usr/bin/env python3\n"
        "import json, os, signal, socket, subprocess, sys, time\n"
        "from pathlib import Path\n"
        "from urllib.parse import urlparse\n"
        "port = int(sys.argv[sys.argv.index('--port') + 1])\n"
        "cfg = json.loads(Path(os.environ['OPENCLAW_CONFIG_PATH']).read_text())\n"
        "provider_port = urlparse(cfg['mock_provider_endpoint']).port\n"
        "child_code = 'import socket,sys,time; s=socket.socket(); s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); s.bind((\\\"127.0.0.1\\\",int(sys.argv[1]))); s.listen(); time.sleep(60)'\n"
        "child = subprocess.Popen([sys.executable, '-c', child_code, str(provider_port)])\n"
        "running = True\n"
        "def stop(*_):\n"
        "    global running; running = False\n"
        "signal.signal(signal.SIGTERM, stop)\n"
        "sock = socket.socket(); sock.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1); sock.bind(('127.0.0.1',port)); sock.listen(); sock.settimeout(.1)\n"
        "try:\n"
        "    while running:\n"
        "        try:\n"
        "            conn,_ = sock.accept(); data = conn.recv(4096); conn.close()\n"
        "            if data:\n"
        "                events = Path(os.environ['OPENCLAW_STATE_DIR']) / 'fake-gateway-events.log'\n"
        "                events.parent.mkdir(parents=True, exist_ok=True)\n"
        "                with events.open('a') as handle: handle.write(data.decode(errors='replace'))\n"
        "        except socket.timeout: pass\n"
        "finally:\n"
        "    sock.close(); child.wait(timeout=3)\n"
    )
    executable.chmod(0o755)
    return root / "fake-python", executable


with tempfile.TemporaryDirectory(prefix="clawgauge-tests-") as raw:
    temp = Path(raw).resolve()
    evidence = temp / "evidence"
    evidence.mkdir()
    gateway_port, provider_port = free_port(), free_port()
    provider_endpoint = f"http://127.0.0.1:{provider_port}/v1"
    config_path = evidence / "prepared-openclaw.json"
    config_path.write_text(json.dumps({"mock_provider_endpoint": provider_endpoint}))
    data = manifest(config_path, gateway_port, provider_endpoint)
    manifest_path = temp / "campaign.json"
    manifest_path.write_text(json.dumps(data))
    loaded = campaign.load_manifest(manifest_path)
    assert len(campaign.schedule(loaded)) == 18
    for unsafe_id in ("../escape", "", ".", "..", "a/b", "a\\b", "a" * 81):
        invalid = json.loads(json.dumps(data))
        invalid["routes"][0]["id"] = unsafe_id
        manifest_path.write_text(json.dumps(invalid))
        try:
            campaign.load_manifest(manifest_path)
        except ValueError:
            pass
        else:
            raise AssertionError("unsafe route id accepted")
    manifest_path.write_text(json.dumps(data))
    assert campaign.execution_blockers(loaded, evidence) == []

    denied_manifest = json.loads(json.dumps(data))
    denied_manifest["pass_env"] = ["OPENCLAW_GATEWAY_TOKEN"]
    manifest_path.write_text(json.dumps(denied_manifest))
    try:
        campaign.load_manifest(manifest_path)
    except ValueError as exc:
        assert "production token" in str(exc)
    else:
        raise AssertionError("production Gateway token was accepted in pass_env")
    manifest_path.write_text(json.dumps(data))

    first_cell = campaign.schedule(loaded)[0]
    base_contract = campaign.cell_contract(loaded, first_cell, "0" * 64)
    base_cell_sha = campaign.digest(base_contract)
    for field, value in {
        "model": "mock/changed",
        "adapter": "changed-adapter",
        "reasoning": "changed-reasoning",
        "fast": True,
        "tools_profile": "changed-tools",
    }.items():
        changed = json.loads(json.dumps(loaded))
        changed["routes"][0][field] = value
        assert campaign.digest(campaign.cell_contract(changed, first_cell, "0" * 64)) != base_cell_sha

    memo_probe = (
        "import asyncio,os,sys\n"
        "from pathlib import Path\n"
        "from clawbench.client import GatewayConfig\n"
        "from clawbench.harness import BenchmarkHarness\n"
        "from clawbench.schemas import TaskRunResult\n"
        "from clawbench.tasks import load_all_tasks\n"
        "root=Path(sys.argv[1]); task=next(t for t in load_all_tasks() if t.id=='t1-bugfix-discount')\n"
        "h=BenchmarkHarness(gateway_config=GatewayConfig(),model='test/model',task_ids=[task.id],runs_per_task=1,randomize_order=False,print_report=False,quiet=True)\n"
        "cache=h._run_cache_path(root,task,0); cache.parent.mkdir(parents=True); cache.write_text(TaskRunResult(task_id=task.id,run_index=0,run_score=.91).model_dump_json())\n"
        "reached=[]\n"
        "def create(*_): reached.append(True); raise RuntimeError('fresh execution reached')\n"
        "h._create_run_workspace=create\n"
        "os.environ['CLAWBENCH_RUN_CACHE_DIR']=str(root); hit=asyncio.run(h._run_single(task,0)); assert hit.run_score==.91 and not reached\n"
        "os.environ['CLAWBENCH_RUN_CACHE_DIR']=''\n"
        "try: asyncio.run(h._run_single(task,0))\n"
        "except RuntimeError as exc: assert str(exc)=='fresh execution reached'\n"
        "else: raise AssertionError('memo bypass did not reach fresh execution')\n"
        "assert reached\n"
    )
    shellbench_available = SHELLBENCH_ROOT.is_dir() and SHELLBENCH_PYTHON.is_file()
    if shellbench_available:
        memo = subprocess.run(
            [str(SHELLBENCH_PYTHON), "-c", memo_probe, str(temp / "memo-cache")],
            cwd=SHELLBENCH_ROOT, capture_output=True, text=True,
        )
        assert memo.returncode == 0, (memo.stdout, memo.stderr)

        aggregate_probe = (
            "from clawbench.client import GatewayConfig\n"
            "from clawbench.harness import BenchmarkHarness\n"
            "from clawbench.schemas import FailureMode,TaskRunResult\n"
            "from clawbench.tasks import load_all_tasks\n"
            "task=next(t for t in load_all_tasks() if t.id=='t1-bugfix-discount')\n"
            "h=BenchmarkHarness(gateway_config=GatewayConfig(),model='test/model',task_ids=[task.id],runs_per_task=1,randomize_order=False,print_report=False,quiet=True)\n"
            "run=TaskRunResult(task_id=task.id,run_index=0,run_score=.75,failure_mode=FailureMode.VERIFICATION_SKIPPED)\n"
            "print(h._aggregate([task],{task.id:[run]}).model_dump_json())\n"
        )
        aggregate = subprocess.run(
            [str(SHELLBENCH_PYTHON), "-c", aggregate_probe], cwd=SHELLBENCH_ROOT,
            capture_output=True, text=True,
        )
        assert aggregate.returncode == 0, (aggregate.stdout, aggregate.stderr)
        native_aggregate = json.loads(aggregate.stdout.strip().splitlines()[-1])
        native_score, native_row = analyzer.one_score(native_aggregate, "t1-bugfix-discount")
        assert native_score == 0.75
        assert native_row["failure_mode_counts"] == {"verification_skipped": 1}
        native_usage = worker.usage_summary(native_aggregate)
        assert native_usage["status"] == "n/a" and native_usage["input_tokens"] is None
    else:
        print("SKIP: optional pinned ShellBench aggregate/memo integration unavailable")

    strict = json.loads(json.dumps(loaded))
    strict["routes"][0]["evidence_tier"] = "strict-decision-grade"
    assert any("strict decision-grade" in item for item in campaign.execution_blockers(strict, evidence))
    subscription = json.loads(json.dumps(loaded))
    subscription["routes"][0]["auth_preparation"]["kind"] = "subscription-handoff"
    assert any("subscription handoff" in item for item in campaign.execution_blockers(subscription, evidence))

    bad = json.loads(json.dumps(data))
    bad["routes"][0]["required_observed_controls"] = []
    manifest_path.write_text(json.dumps(bad))
    try:
        campaign.load_manifest(manifest_path)
    except ValueError:
        pass
    else:
        raise AssertionError("dropping required proof controls was accepted")

    # Canonical evidence may live under ~/.openclaw; mutable runtime may not collide
    # with actual production config/auth/agent trees.
    runtime = temp / "runtime-validation"
    cell = runtime / "cell"
    config_copy = cell / "openclaw.json"
    cell.mkdir(parents=True)
    config_copy.write_bytes(config_path.read_bytes())
    canonical_evidence = Path.home() / ".openclaw" / "workspace" / "skills" / "clawgauge" / "runs" / "proof"
    base_spec = {
        "run_root": str(canonical_evidence.parent),
        "runtime_root": str(runtime),
        "cell_root": str(cell),
        "evidence_root": str(canonical_evidence),
        "home": str(cell / "home"),
        "state_dir": str(cell / "state"),
        "config_path": str(config_copy),
        "workspace_root": str(cell / "state" / "workspace-clawbench"),
        "output_path": str(canonical_evidence / "native-result.json"),
        "gateway_url": f"ws://127.0.0.1:{gateway_port}",
        "gateway_command": ["/tmp/openclaw", "gateway", "run", "--bind", "loopback", "--port", str(gateway_port)],
        "adapter": "openclaw",
        "provider": "mock",
        "model": "mock/a",
        "task": "t1-bugfix-discount",
        "evidence_tier": "requested-route-screening",
        "required_observed_controls": list(campaign.REQUIRED_CONTROLS),
        "independently_observed_controls": [],
        "auth_preparation": loaded["routes"][0]["auth_preparation"],
        "task_fingerprint": "0" * 64,
        "cell_contract": {"test": "base"},
    }
    base_spec["cell_sha256"] = worker.object_sha256(base_spec["cell_contract"])
    worker.validate_spec(base_spec)

    for bad_url in (
        "ws://localhost:18789",
        "ws://127.0.0.1:18789",
        "ws://[::1]:18789",
        "ws://production-gateway.invalid:18789",
    ):
        unsafe_endpoint = dict(base_spec)
        unsafe_endpoint["gateway_url"] = bad_url
        try:
            worker.validate_spec(unsafe_endpoint)
        except ValueError:
            pass
        else:
            raise AssertionError(f"production endpoint was accepted: {bad_url}")

    unsafe = dict(base_spec)
    unsafe["state_dir"] = str(Path.home() / ".openclaw" / "agents")
    try:
        worker.validate_spec(unsafe)
    except ValueError:
        pass
    else:
        raise AssertionError("production agent tree was accepted")

    for key, value in {
        "home": Path.home() / ".openclaw",
        "state_dir": Path.home() / ".openclaw" / "agents",
        "config_path": Path.home() / ".openclaw" / "openclaw.json",
    }.items():
        colliding = dict(base_spec)
        colliding[key] = str(value)
        try:
            worker.validate_spec(colliding)
        except ValueError:
            pass
        else:
            raise AssertionError(f"production root was accepted for {key}")

    symlink_root = temp / "symlink-openclaw"
    symlink_root.symlink_to(Path.home() / ".openclaw", target_is_directory=True)
    symlinked = dict(base_spec)
    symlinked["state_dir"] = str(symlink_root / "agents")
    try:
        worker.validate_spec(symlinked)
    except ValueError:
        pass
    else:
        raise AssertionError("symlinked production state root was accepted")

    # Three genuinely fresh worker lifecycles hit a fake Gateway and fake provider.
    fake_python, fake_openclaw = write_fake_stack(temp)
    before = production_snapshot()
    fresh_workspaces = []
    for repetition in range(1, 4):
        runtime_root = temp / f"runtime-r{repetition}"
        cell_root = runtime_root / "cell"
        evidence_root = evidence / f"r{repetition}"
        cell_root.mkdir(parents=True)
        evidence_root.mkdir()
        copied = cell_root / "openclaw.json"
        copied.write_bytes(config_path.read_bytes())
        spec = dict(base_spec)
        spec.update(
            {
                "run_root": str(evidence),
                "runtime_root": str(runtime_root),
                "cell_root": str(cell_root),
                "evidence_root": str(evidence_root),
                "home": str(cell_root / "home"),
                "state_dir": str(cell_root / "state"),
                "config_path": str(copied),
                "workspace_root": str(cell_root / "state" / "workspace-clawbench"),
                "output_path": str(evidence_root / "native-result.json"),
                "gateway_command": [str(fake_openclaw), "gateway", "run", "--bind", "loopback", "--port", str(gateway_port)],
                "repetition": repetition,
            }
        )
        spec_path = evidence_root / "cell.json"
        spec_path.write_text(json.dumps(spec))
        env = {"PATH": os.defpath, "LANG": "C.UTF-8", "PYTHONPATH": str(fake_python)}
        run = subprocess.run(
            [sys.executable, str(ROOT / "personal_campaign_worker.py"), "--cell", str(spec_path)],
            cwd=cell_root,
            env=env,
            capture_output=True,
            text=True,
            timeout=10,
        )
        assert run.returncode == 0, (run.stdout, run.stderr)
        receipt = json.loads((evidence_root / "worker-receipt.json").read_text())
        result = json.loads((evidence_root / "native-result.json").read_text())
        assert receipt["memo_env_at_harness_entry"] == ""
        assert receipt["effective_route_proof"] == "unavailable"
        assert receipt["claim_scope"] == "requested-route-screening"
        assert receipt["usage"]["input_tokens"] is None
        assert receipt["usage"]["output_tokens"] == 7
        assert receipt["usage"]["reasoning_tokens"] is None
        assert receipt["usage"]["cost_usd"] is None
        assert receipt["usage"]["status"] == "partial"
        assert result["task_results"][0]["mean_run_score"] == 0.75
        assert list((cell_root / "state" / "workspace-clawbench").glob("*/executed"))
        assert "agents.create" in (cell_root / "state" / "fake-gateway-events.log").read_text()
        fresh_workspaces.append(receipt["fresh_workspace_root"])
        assert receipt["task_fingerprint"] == "0" * 64
        assert not worker.listener_open("127.0.0.1", gateway_port)
        assert not worker.listener_open("127.0.0.1", provider_port)
    assert len(set(fresh_workspaces)) == 3
    assert production_snapshot() == before

    # The real supervisor executes and retains the full 18-cell fake matrix.
    fake_shellbench = fake_python
    pycache = fake_shellbench / "clawbench" / "__pycache__"
    if pycache.is_dir():
        for cached in pycache.iterdir():
            cached.unlink()
        pycache.rmdir()
    (fake_shellbench / ".gitignore").write_text("__pycache__/\n*.pyc\n")
    for task_id in campaign.TASKS:
        (fake_shellbench / f"{task_id}.yaml").write_text(f"id: {task_id}\n")
    subprocess.run(["git", "init", "-q"], cwd=fake_shellbench, check=True)
    subprocess.run(["git", "add", "."], cwd=fake_shellbench, check=True)
    subprocess.run(
        ["git", "-c", "user.name=ClawGauge Test", "-c", "user.email=test@example.invalid", "commit", "-qm", "fixture"],
        cwd=fake_shellbench, check=True,
    )
    fake_commit = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=fake_shellbench, check=True,
        capture_output=True, text=True,
    ).stdout.strip()
    full_run = temp / "full-campaign"
    full_run.mkdir()
    full_config = full_run / "prepared-openclaw.json"
    full_config.write_bytes(config_path.read_bytes())
    full_manifest = manifest(full_config, gateway_port, provider_endpoint)
    full_manifest["gateway"]["executable"] = str(fake_openclaw)
    full_manifest["shellbench"] = {"root": str(fake_shellbench), "commit": fake_commit, "python": str(CAMPAIGN_PYTHON)}
    full_manifest_path = temp / "full-campaign.json"
    full_manifest_path.write_text(json.dumps(full_manifest))
    full_env = {"PATH": os.defpath, "LANG": "C.UTF-8"}
    full = subprocess.run(
        [sys.executable, str(ROOT / "run_personal_campaign.py"), "--manifest", str(full_manifest_path),
         "--run-dir", str(full_run), "--execute", "--armed"],
        env=full_env, capture_output=True, text=True, timeout=30,
    )
    assert full.returncode == 0, (full.stdout, full.stderr)
    supervisors = sorted((full_run / "cells").glob("*/supervisor-receipt.json"))
    workers = sorted((full_run / "cells").glob("*/worker-receipt.json"))
    assert len(supervisors) == len(workers) == 18
    assert all(json.loads(path.read_text())["exit_code"] == 0 for path in supervisors)
    campaign_receipt = json.loads((full_run / "campaign-receipt.json").read_text())
    assert campaign_receipt == {"attempted_cells": 18, "campaign_timed_out": False, "failed_cells": 0, "runtime_root_removed": True}
    assert not (fake_shellbench / ".clawbench").exists()
    assert not (fake_shellbench / "results").exists()
    assert all("--profile" not in json.loads(path.with_name("cell.json").read_text())["gateway_command"] for path in supervisors)
    comparison_json = full_run / "comparison.json"
    comparison_md = full_run / "comparison.md"
    analyzed = subprocess.run(
        [sys.executable, str(ROOT / "analyze_personal_campaign.py"), "--run-dir", str(full_run),
         "--out", str(comparison_md), "--json", str(comparison_json)],
        env=full_env, capture_output=True, text=True,
    )
    assert analyzed.returncode == 0, (analyzed.stdout, analyzed.stderr)
    comparison = json.loads(comparison_json.read_text())
    assert comparison["verdict"] == "requested-route-screening-complete"
    assert comparison["confidence"] == "directional-requested-route"
    assert comparison["scored_cells"] == 18
    assert comparison["effective_route_verified_cells"] == 0
    assert len(comparison["effective_route_proof_gaps"]) == 18
    assert comparison["actual_usage"]["reasoning_tokens"] is None
    assert production_snapshot() == before

    quality_native = workers[0].with_name("native-result.json")
    quality_worker = workers[0]
    quality_worker_original = quality_worker.read_text()
    quality_original = quality_native.read_text()
    quality_payload = json.loads(quality_original)
    quality_payload["task_results"][0]["failure_mode_counts"] = {"verification_skipped": 1}
    quality_native.write_text(json.dumps(quality_payload))
    quality_worker_payload = json.loads(quality_worker_original)
    quality_worker_payload["native_result_sha256"] = digest(quality_native)
    quality_worker.write_text(json.dumps(quality_worker_payload))
    quality_json = temp / "quality-comparison.json"
    quality_md = temp / "quality-comparison.md"
    quality = subprocess.run(
        [sys.executable, str(ROOT / "analyze_personal_campaign.py"), "--run-dir", str(full_run),
         "--out", str(quality_md), "--json", str(quality_json)],
        env=full_env, capture_output=True, text=True,
    )
    assert quality.returncode == 0
    quality_result = json.loads(quality_json.read_text())
    assert quality_result["verdict"] == "requested-route-screening-complete"
    assert quality_result["confidence"] == "directional-requested-route"
    assert quality_result["scored_cells"] == 18
    assert json.loads(quality_json.read_text())["failure_categories"] == {"quality_failure": 1}
    assert quality_native.exists() and "verification_skipped" in quality_native.read_text()
    quality_native.write_text(quality_original)
    quality_worker.write_text(quality_worker_original)

    mismatch_payload = json.loads(quality_original)
    mismatch_payload["model"] = "mock/wrong-route"
    quality_native.write_text(json.dumps(mismatch_payload))
    mismatch_receipt = json.loads(quality_worker_original)
    mismatch_receipt["native_result_sha256"] = digest(quality_native)
    quality_worker.write_text(json.dumps(mismatch_receipt))
    mismatch_json = temp / "mismatch.json"
    mismatch = subprocess.run(
        [sys.executable, str(ROOT / "analyze_personal_campaign.py"), "--run-dir", str(full_run),
         "--out", str(temp / "mismatch.md"), "--json", str(mismatch_json)],
        env=full_env, capture_output=True, text=True,
    )
    assert mismatch.returncode == 2
    assert any("label mismatch" in item for item in json.loads(mismatch_json.read_text())["blockers"])
    quality_native.write_text(quality_original)
    quality_worker.write_text(quality_worker_original)

    # A scored native transport failure is infra-classified without discarding its score.
    infra_payload = json.loads(quality_original)
    infra_payload["task_results"][0]["failure_mode_counts"] = {"environment_unavailable": 1}
    quality_native.write_text(json.dumps(infra_payload))
    infra_worker = json.loads(quality_worker_original)
    infra_worker["native_result_sha256"] = digest(quality_native)
    quality_worker.write_text(json.dumps(infra_worker))
    infra_json = temp / "scored-infra-comparison.json"
    infra = subprocess.run(
        [sys.executable, str(ROOT / "analyze_personal_campaign.py"), "--run-dir", str(full_run),
         "--out", str(temp / "scored-infra-comparison.md"), "--json", str(infra_json)],
        env=full_env, capture_output=True, text=True,
    )
    assert infra.returncode == 2
    infra_result = json.loads(infra_json.read_text())
    assert infra_result["failure_categories"] == {"scored_infra_failure": 1}
    assert infra_result["verdict"] == "blocked"
    assert infra_result["scored_cells"] == 18
    quality_native.write_text(quality_original)
    quality_worker.write_text(quality_worker_original)

    # Binding tampering is rejected before scores are trusted.
    bound_supervisor = supervisors[0]
    bound_original = bound_supervisor.read_text()
    bound_payload = json.loads(bound_original)
    bound_payload["cell_sha256"] = "0" * 64
    bound_supervisor.write_text(json.dumps(bound_payload))
    binding_json = temp / "binding-comparison.json"
    binding = subprocess.run(
        [sys.executable, str(ROOT / "analyze_personal_campaign.py"), "--run-dir", str(full_run),
         "--out", str(temp / "binding-comparison.md"), "--json", str(binding_json)],
        env=full_env, capture_output=True, text=True,
    )
    assert binding.returncode == 2
    assert any("identity binding mismatch" in item for item in json.loads(binding_json.read_text())["blockers"])
    bound_supervisor.write_text(bound_original)

    # Nonfinite native scores remain rejected even with a matching artifact digest.
    nonfinite_original = quality_native.read_text()
    nonfinite_worker_original = quality_worker.read_text()
    nonfinite_payload = json.loads(nonfinite_original)
    nonfinite_payload["task_results"][0]["mean_run_score"] = float("nan")
    quality_native.write_text(json.dumps(nonfinite_payload))
    nonfinite_worker = json.loads(nonfinite_worker_original)
    nonfinite_worker["native_result_sha256"] = digest(quality_native)
    quality_worker.write_text(json.dumps(nonfinite_worker))
    nonfinite_json = temp / "nonfinite-comparison.json"
    nonfinite = subprocess.run(
        [sys.executable, str(ROOT / "analyze_personal_campaign.py"), "--run-dir", str(full_run),
         "--out", str(temp / "nonfinite-comparison.md"), "--json", str(nonfinite_json)],
        env=full_env, capture_output=True, text=True,
    )
    assert nonfinite.returncode == 2
    assert any("finite" in item for item in json.loads(nonfinite_json.read_text())["blockers"])
    quality_native.write_text(nonfinite_original)
    quality_worker.write_text(nonfinite_worker_original)

    # A whole-campaign deadline retains the attempted cell and prevents the next launch.
    deadline_run = temp / "deadline-campaign"
    deadline_run.mkdir()
    deadline_config = deadline_run / "prepared-openclaw.json"
    deadline_config.write_text(json.dumps({
        "mock_provider_endpoint": provider_endpoint,
        "sleep_seconds": 2,
    }))
    deadline_manifest = manifest(deadline_config, gateway_port, provider_endpoint)
    deadline_manifest["gateway"]["executable"] = str(fake_openclaw)
    deadline_manifest["shellbench"] = full_manifest["shellbench"]
    deadline_manifest["bounds"]["cell_timeout_seconds"] = 5
    deadline_manifest["bounds"]["campaign_timeout_seconds"] = 1
    deadline_manifest_path = temp / "deadline-campaign.json"
    deadline_manifest_path.write_text(json.dumps(deadline_manifest))
    deadline = subprocess.run(
        [sys.executable, str(ROOT / "run_personal_campaign.py"), "--manifest", str(deadline_manifest_path),
         "--run-dir", str(deadline_run), "--execute", "--armed"],
        env=full_env, capture_output=True, text=True, timeout=10,
    )
    assert deadline.returncode == 124, (deadline.stdout, deadline.stderr)
    deadline_receipt = json.loads((deadline_run / "campaign-receipt.json").read_text())
    assert deadline_receipt["attempted_cells"] == 1
    assert deadline_receipt["campaign_timed_out"] is True
    assert len(list((deadline_run / "cells").glob("*/supervisor-receipt.json"))) == 1

    # Frozen files detect drift, and one synthetic route failure does not discard later cells.
    frozen_manifest_path = full_run / "manifest.json"
    frozen_manifest_original = frozen_manifest_path.read_text()
    frozen_manifest = json.loads(frozen_manifest_original)
    frozen_manifest["campaign_id"] = "drifted"
    frozen_manifest_path.write_text(json.dumps(frozen_manifest))
    try:
        campaign.verify_frozen(full_manifest, full_run, campaign.schedule(full_manifest))
    except RuntimeError as exc:
        assert "drift" in str(exc)
    else:
        raise AssertionError("frozen manifest drift was accepted")
    frozen_manifest_path.write_text(frozen_manifest_original)
    frozen_verified_manifest = json.loads(frozen_manifest_path.read_text())

    frozen_task = fake_shellbench / f"{campaign.TASKS[0]}.yaml"
    frozen_task_original = frozen_task.read_text()
    try:
        frozen_task.write_text(frozen_task_original + "# drift\n")
        try:
            campaign.verify_frozen(frozen_verified_manifest, full_run, campaign.schedule(frozen_verified_manifest))
        except RuntimeError as exc:
            assert "task bytes drift" in str(exc)
        else:
            raise AssertionError("frozen task-byte drift was accepted")
    finally:
        frozen_task.write_text(frozen_task_original)

    dirty_probe = fake_shellbench / "unexpected-untracked"
    try:
        dirty_probe.write_text("dirty")
        try:
            campaign.verify_frozen(frozen_verified_manifest, full_run, campaign.schedule(frozen_verified_manifest))
        except RuntimeError as exc:
            assert "no longer clean" in str(exc)
        else:
            raise AssertionError("dirty pinned checkout was accepted")
    finally:
        dirty_probe.unlink(missing_ok=True)

    partial_run = temp / "partial-campaign"
    partial_run.mkdir()
    partial_config = partial_run / "prepared-openclaw.json"
    partial_config.write_text(json.dumps({
        "mock_provider_endpoint": provider_endpoint,
        "fail_model": "mock/b",
        "fail_task": "t1-bugfix-discount",
    }))
    partial_manifest = manifest(partial_config, gateway_port, provider_endpoint)
    partial_manifest["gateway"]["executable"] = str(fake_openclaw)
    partial_manifest["shellbench"] = full_manifest["shellbench"]
    partial_manifest_path = temp / "partial-campaign.json"
    partial_manifest_path.write_text(json.dumps(partial_manifest))
    partial = subprocess.run(
        [sys.executable, str(ROOT / "run_personal_campaign.py"), "--manifest", str(partial_manifest_path),
         "--run-dir", str(partial_run), "--execute", "--armed"],
        env=full_env, capture_output=True, text=True, timeout=30,
    )
    assert partial.returncode == 1, (partial.stdout, partial.stderr)
    partial_supervisors = sorted((partial_run / "cells").glob("*/supervisor-receipt.json"))
    partial_workers = sorted((partial_run / "cells").glob("*/worker-receipt.json"))
    assert len(partial_supervisors) == 18, (len(partial_supervisors), partial.stdout, partial.stderr)
    assert sum(json.loads(path.read_text())["exit_code"] != 0 for path in partial_supervisors) == 3
    assert len(partial_workers) == 15
    partial_receipt = json.loads((partial_run / "campaign-receipt.json").read_text())
    assert partial_receipt["attempted_cells"] == 18 and partial_receipt["failed_cells"] == 3
    partial_json = temp / "partial-comparison.json"
    partial_md = temp / "partial-comparison.md"
    partial_analysis = subprocess.run(
        [sys.executable, str(ROOT / "analyze_personal_campaign.py"), "--run-dir", str(partial_run),
         "--out", str(partial_md), "--json", str(partial_json)],
        env=full_env, capture_output=True, text=True,
    )
    assert partial_analysis.returncode == 2
    assert json.loads(partial_json.read_text())["failure_categories"]["infra_failure"] == 3
    assert all(path.with_name("worker.log").is_file() for path in partial_supervisors)
    assert production_snapshot() == before

    # The worker rejects inherited production-key names before creating runtime state.
    denied_runtime = temp / "denied-runtime"
    denied_cell = denied_runtime / "cell"
    denied_evidence = evidence / "denied"
    denied_cell.mkdir(parents=True)
    denied_evidence.mkdir()
    denied_config = denied_cell / "openclaw.json"
    denied_config.write_bytes(config_path.read_bytes())
    denied_spec = dict(base_spec)
    denied_spec.update({
        "run_root": str(evidence), "runtime_root": str(denied_runtime), "cell_root": str(denied_cell),
        "evidence_root": str(denied_evidence), "home": str(denied_cell / "home"),
        "state_dir": str(denied_cell / "state"), "config_path": str(denied_config),
        "workspace_root": str(denied_cell / "state" / "workspace-clawbench"),
        "output_path": str(denied_evidence / "native-result.json"),
    })
    denied_path = denied_evidence / "cell.json"
    denied_path.write_text(json.dumps(denied_spec))
    denied_env = {"PATH": os.defpath, "OPENAI_API_KEY": "test-denied"}
    denied = subprocess.run([sys.executable, str(ROOT / "personal_campaign_worker.py"), "--cell", str(denied_path)], env=denied_env, capture_output=True, text=True)
    assert denied.returncode == 78 and "production credential environment" in denied.stderr
    assert not (denied_cell / "home").exists()

    # Supervisor timeout kills a whole process group, including its child.
    log = temp / "timeout.log"
    pid_file = temp / "child.pid"
    nested_port = free_port()
    child_code = (
        "import os,pathlib,signal,socket,sys,time;"
        "signal.signal(signal.SIGTERM,signal.SIG_IGN);"
        "s=socket.socket();s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);"
        "s.bind(('127.0.0.1',int(sys.argv[1])));s.listen();"
        f"pathlib.Path({str(pid_file)!r}).write_text(str(os.getpid()));time.sleep(30)"
    )
    code = (
        "import subprocess,sys,time;"
        f"subprocess.Popen([sys.executable,'-c',{child_code!r},{str(nested_port)!r}],start_new_session=True);"
        "time.sleep(30)"
    )
    child_pid = None
    try:
        exit_code, timed_out, elapsed = campaign.execute_process_group(
            [sys.executable, "-c", code], cwd=temp, env={"PATH": os.defpath},
            log_path=log, timeout_seconds=0.3, grace_seconds=1,
        )
        assert exit_code == 124 and timed_out and elapsed < 4
        child_pid = int(pid_file.read_text())
        assert not worker.listener_open("127.0.0.1", nested_port)
        deadline = time.monotonic() + 2
        while time.monotonic() < deadline:
            probe = subprocess.run(
                ["ps", "-o", "stat=", "-p", str(child_pid)], capture_output=True, text=True
            )
            if not probe.stdout.strip() or probe.stdout.strip().startswith("Z"):
                break
            time.sleep(0.05)
        else:
            raise AssertionError("process-group timeout left a TERM-resistant child")
    finally:
        if child_pid is None and pid_file.exists():
            child_pid = int(pid_file.read_text())
        if child_pid is not None:
            try:
                os.killpg(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass

print("ClawGauge personal campaign safety tests: PASS")
