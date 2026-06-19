"""Agent harness adapter + a minimal reference implementation.

`AgentHarness` is the swappable seam described in the architecture: the MVP ships
`SimpleAgent`, but a wrapped open framework (LangGraph, etc.) can implement the
same interface without changing the workflow.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from .models_router import Router


@dataclass
class Proposal:
    patch_text: str
    rationale: str
    prompt_tokens: int
    completion_tokens: int


SYSTEM_PROMPT = (
    "You are a software engineering agent operating inside a regulated boundary. "
    "Given a task and (on retries) the failing test output, return a single unified "
    "diff that makes the test suite pass. Output only the patch."
)


class AgentHarness(Protocol):
    async def propose(self, *, intent: str, iteration: int, feedback: dict | None) -> Proposal:
        ...


class SimpleAgent:
    """Thin single-model loop. The reliability runtime (gate + critic) lives in
    the workflow, not here — that separation is the point."""

    def __init__(self, router: Router):
        self.router = router
        self.client = router.client()
        self._history: list[dict[str, str]] = [{"role": "system", "content": SYSTEM_PROMPT}]

    async def propose(self, *, intent: str, iteration: int, feedback: dict | None) -> Proposal:
        if iteration == 0:
            self._history.append({"role": "user", "content": f"Task: {intent}"})
        else:
            self._history.append(
                {"role": "user", "content": f"The gate failed. Output:\n{feedback}\nFix it."}
            )
        resp = await self.client.complete(self._history)
        self._history.append({"role": "assistant", "content": resp.text})
        return Proposal(
            patch_text=resp.text,
            rationale=f"iteration {iteration}",
            prompt_tokens=resp.prompt_tokens,
            completion_tokens=resp.completion_tokens,
        )
