#!/usr/bin/env python3
"""Bounded cleanup for a subprocess and all descendant process groups."""
from __future__ import annotations

import os
import signal
import subprocess
import time


def descendant_process_groups(root_pid: int) -> set[int]:
    """Snapshot process groups for ``root_pid`` and all current descendants."""
    result = subprocess.run(
        ["ps", "-axo", "pid=,ppid=,pgid="], capture_output=True, text=True, check=True
    )
    children: dict[int, list[tuple[int, int]]] = {}
    root_group: int | None = None
    for line in result.stdout.splitlines():
        try:
            pid, ppid, pgid = (int(value) for value in line.split())
        except ValueError:
            continue
        children.setdefault(ppid, []).append((pid, pgid))
        if pid == root_pid:
            root_group = pgid
    groups = {root_group or root_pid}
    pending = [root_pid]
    seen = {root_pid}
    while pending:
        parent = pending.pop()
        for pid, pgid in children.get(parent, []):
            groups.add(pgid)
            if pid not in seen:
                seen.add(pid)
                pending.append(pid)
    return groups


def _signal_groups(groups: set[int], sig: signal.Signals) -> None:
    own_group = os.getpgrp()
    for pgid in sorted(groups, reverse=True):
        if pgid == own_group:
            continue
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            pass


def _group_alive(pgid: int) -> bool:
    if pgid == os.getpgrp():
        return False
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def terminate_process_tree(process: subprocess.Popen[str], grace_seconds: float) -> None:
    """TERM, then KILL every captured group even when the direct parent exits early."""
    groups = descendant_process_groups(process.pid)
    _signal_groups(groups, signal.SIGTERM)
    deadline = time.monotonic() + grace_seconds
    while time.monotonic() < deadline:
        try:
            process.wait(timeout=min(0.05, max(0.0, deadline - time.monotonic())))
        except subprocess.TimeoutExpired:
            pass
        time.sleep(0.02)
        if not any(_group_alive(group) for group in groups):
            return
    _signal_groups(groups, signal.SIGKILL)
    kill_deadline = time.monotonic() + grace_seconds
    while time.monotonic() < kill_deadline:
        try:
            process.wait(timeout=min(0.05, max(0.0, kill_deadline - time.monotonic())))
        except subprocess.TimeoutExpired:
            pass
        if not any(_group_alive(group) for group in groups):
            return
        time.sleep(0.02)
