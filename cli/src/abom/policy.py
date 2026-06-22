"""Simple JSON policy engine (MVP).

Phase-2 replaces this module with OPA/Rego behind the same function signatures.
"""
from __future__ import annotations

import fnmatch
from typing import Any

DEFAULT_POLICY: dict[str, Any] = {
    "name": "default",
    "allowed_models": ["local/qwen2.5-coder"],
    "egress_allowed": False,
    "consequential_actions": ["writes_outside_workspace", "touches_paths:**/auth/**"],
    "approval_required_for_consequential": True,
    "max_iterations_cap": 8,
}


def model_allowed(policy: dict, model: str) -> bool:
    return model in policy.get("allowed_models", [])


def egress_allowed(policy: dict) -> bool:
    return bool(policy.get("egress_allowed", False))


def is_consequential(policy: dict, proposal: dict) -> bool:
    """proposal = {"changed_paths": [...], "writes_outside_workspace": bool}."""
    rules = policy.get("consequential_actions", [])
    if proposal.get("writes_outside_workspace") and "writes_outside_workspace" in rules:
        return True
    for rule in rules:
        if rule.startswith("touches_paths:"):
            pattern = rule.split(":", 1)[1]
            for path in proposal.get("changed_paths", []):
                if fnmatch.fnmatch(path, pattern):
                    return True
    return False


def approval_required(policy: dict, proposal: dict) -> bool:
    return (
        policy.get("approval_required_for_consequential", True)
        and is_consequential(policy, proposal)
    )
