"""Model router + client.

MVP: routes everything to the single local OpenAI-compatible endpoint (vLLM).
The Router is where Phase-2 adds data-sensitivity classification and the gated
egress path; the interface stays the same.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx

from .config import settings
from . import policy as policy_mod


@dataclass
class ModelResponse:
    text: str
    prompt_tokens: int
    completion_tokens: int
    model: str


class ModelClient:
    """OpenAI-compatible chat client."""

    def __init__(self, base_url: str, model: str):
        self.base_url = base_url.rstrip("/")
        self.model = model

    async def complete(self, messages: list[dict[str, str]], **kw: Any) -> ModelResponse:
        async with httpx.AsyncClient(timeout=120) as client:
            resp = await client.post(
                f"{self.base_url}/chat/completions",
                json={"model": self.model, "messages": messages, **kw},
            )
            resp.raise_for_status()
            data = resp.json()
        usage = data.get("usage", {})
        return ModelResponse(
            text=data["choices"][0]["message"]["content"],
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            model=self.model,
        )


class MockModelClient:
    """Deterministic stand-in so the stack runs on a laptop without a GPU.

    Returns a trivially-correct unified diff for the seeded demo task and a
    deliberately-broken one on the first attempt to exercise the critic loop.
    """

    def __init__(self, model: str):
        self.model = model

    async def complete(self, messages: list[dict[str, str]], **kw: Any) -> ModelResponse:
        attempt = sum(1 for m in messages if m["role"] == "assistant")
        if attempt == 0:
            text = "PATCH:\n*** broken on purpose (missing import) ***"
        else:
            text = "PATCH:\n*** corrected patch passing the gate ***"
        return ModelResponse(text=text, prompt_tokens=128, completion_tokens=64, model=self.model)


class Router:
    def __init__(self, pol: dict | None = None):
        self.policy = pol or policy_mod.DEFAULT_POLICY

    def select(self, *, task: str, sensitivity: str = "high") -> tuple[str, bool]:
        """Return (model_name, is_local). MVP always local; never egress."""
        model = settings.model_name
        if not policy_mod.model_allowed(self.policy, model):
            raise PermissionError(f"model {model} not allowed by policy")
        # sensitivity high -> must stay local. egress disabled in MVP.
        return model, True

    def client(self) -> ModelClient | MockModelClient:
        if settings.model_use_mock:
            return MockModelClient(settings.model_name)
        return ModelClient(settings.model_base_url, settings.model_name)
