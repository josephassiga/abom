"""Sandbox runner + the build/test gate.

MVP sandbox = a constrained subprocess in an ephemeral workspace. The Sandbox
interface is intentionally stable so Phase-2 can swap in gVisor / Kata microVMs
without touching callers.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import time
import uuid
from dataclasses import dataclass, field

from .config import settings


@dataclass
class GateOutcome:
    status: str            # pass|fail
    exit_code: int
    duration_ms: int
    stdout: str
    stderr: str
    details: dict = field(default_factory=dict)


class Sandbox:
    """Ephemeral workspace. Phase-2: replace _run with a microVM executor."""

    def __init__(self, run_id: str):
        self.run_id = str(run_id)
        self.path = os.path.join(settings.workspace_root, f"{self.run_id}-{uuid.uuid4().hex[:8]}")
        os.makedirs(self.path, exist_ok=True)

    def materialize(self, repo_url: str) -> None:
        """Clone / copy the target repo into the workspace (no network egress in real impl
        beyond the customer's own git). MVP: local path or git clone."""
        if os.path.isdir(repo_url):
            shutil.copytree(repo_url, os.path.join(self.path, "repo"), dirs_exist_ok=True)
        else:
            self._run(["git", "clone", "--depth", "1", repo_url, "repo"])

    def apply_patch(self, patch_text: str) -> dict:
        """Apply an agent-proposed change. MVP placeholder: write the patch to disk.
        Real impl: `git apply` and compute changed_paths."""
        patch_file = os.path.join(self.path, "proposal.patch")
        with open(patch_file, "w") as fh:
            fh.write(patch_text)
        # TODO: git apply + parse changed paths
        return {"changed_paths": [], "writes_outside_workspace": False}

    def run_gate(self, test_command: str) -> GateOutcome:
        start = time.monotonic()
        proc = self._run(test_command.split(), cwd=os.path.join(self.path, "repo"),
                         timeout=settings.gate_timeout_seconds, check=False)
        dur = int((time.monotonic() - start) * 1000)
        status = "pass" if proc.returncode == 0 else "fail"
        return GateOutcome(
            status=status, exit_code=proc.returncode, duration_ms=dur,
            stdout=(proc.stdout or "")[-8000:], stderr=(proc.stderr or "")[-8000:],
            details={"command": test_command},
        )

    def cleanup(self) -> None:
        shutil.rmtree(self.path, ignore_errors=True)

    def _run(self, cmd, cwd=None, timeout=120, check=True):
        return subprocess.run(
            cmd, cwd=cwd or self.path, capture_output=True, text=True,
            timeout=timeout, check=check,
        )
