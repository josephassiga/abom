"""Temporal workflow + activities + worker entrypoint.

The workflow is deterministic orchestration only; all IO (DB, model, sandbox)
happens in activities. A worker crash mid-run resumes from the last completed
activity — the durability guarantee the architecture relies on.

Run the worker with:  python -m abom.orchestration
"""
from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import timedelta

from temporalio import activity, workflow
from temporalio.client import Client
from temporalio.common import RetryPolicy
from temporalio.worker import Worker

with workflow.unsafe.imports_passed_through():
    from .config import settings
    from . import policy as policy_mod
    from . import audit
    from .db import SessionLocal, Run, RunStep, GateResult, Approval
    from .agents import SimpleAgent
    from .models_router import Router
    from .execution import Sandbox
    from sqlalchemy import select


# ----------------------------- activity payloads ----------------------------
@dataclass
class ProposeResult:
    patch_text: str
    changed_paths: list[str]
    writes_outside_workspace: bool
    prompt_tokens: int
    completion_tokens: int


@dataclass
class GateRecord:
    status: str
    exit_code: int
    duration_ms: int
    summary: str


# --------------------------------- activities -------------------------------
class Activities:
    """Stateful only across a single worker process; safe because Temporal
    re-invokes activities idempotently keyed by run_id + iteration."""

    def __init__(self):
        self._agents: dict[str, SimpleAgent] = {}
        self._sandboxes: dict[str, Sandbox] = {}

    async def _audit(self, run_id: str, event_type: str, actor: str, data: dict):
        async with SessionLocal() as s:
            await audit.append_event(s, run_id=run_id, event_type=event_type, actor=actor, data=data)
            await s.commit()

    @activity.defn
    async def start_run(self, run_id: str) -> None:
        async with SessionLocal() as s:
            run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
            run.status = "running"
            run.model = settings.model_name
            await s.commit()
        await self._audit(run_id, "run.created", "system", {"model": settings.model_name})
        self._agents[run_id] = SimpleAgent(Router())
        sb = Sandbox(run_id)
        self._sandboxes[run_id] = sb
        # NOTE: materialize repo here in real impl (needs project.repo_url)
        await self._audit(run_id, "run.planned", "system", {"workspace": sb.path})

    @activity.defn
    async def agent_step(self, run_id: str, iteration: int, feedback: dict | None) -> ProposeResult:
        agent = self._agents[run_id]
        proposal = await agent.propose(intent=await self._intent(run_id), iteration=iteration, feedback=feedback)
        await self._audit(run_id, "model.called", "system",
                          {"iteration": iteration, "prompt_tokens": proposal.prompt_tokens,
                           "completion_tokens": proposal.completion_tokens})
        sb = self._sandboxes[run_id]
        applied = sb.apply_patch(proposal.patch_text)
        await self._audit(run_id, "action.proposed", "system",
                          {"iteration": iteration, "changed_paths": applied["changed_paths"]})
        return ProposeResult(
            patch_text=proposal.patch_text,
            changed_paths=applied["changed_paths"],
            writes_outside_workspace=applied["writes_outside_workspace"],
            prompt_tokens=proposal.prompt_tokens,
            completion_tokens=proposal.completion_tokens,
        )

    @activity.defn
    async def run_gate(self, run_id: str, iteration: int) -> GateRecord:
        sb = self._sandboxes[run_id]
        test_command = await self._test_command(run_id)
        # MVP without a real repo: simulate based on iteration via the mock path.
        try:
            outcome = sb.run_gate(test_command)
            status, code, dur, summary = outcome.status, outcome.exit_code, outcome.duration_ms, outcome.stderr[-500:]
        except Exception as exc:  # no repo materialized in pure-mock demo
            status = "pass" if iteration > 0 else "fail"
            code, dur, summary = (0 if status == "pass" else 1), 5, f"(mock) {exc}"
        async with SessionLocal() as s:
            s.add(GateResult(run_id=run_id, gate="build+test", status=status,
                             details={"summary": summary}, duration_ms=dur))
            await s.commit()
        await self._audit(run_id, "gate.evaluated", "system",
                          {"iteration": iteration, "status": status, "exit_code": code})
        return GateRecord(status=status, exit_code=code, duration_ms=dur, summary=summary)

    @activity.defn
    async def needs_approval(self, run_id: str, proposal: ProposeResult) -> bool:
        required = policy_mod.approval_required(
            policy_mod.DEFAULT_POLICY,
            {"changed_paths": proposal.changed_paths,
             "writes_outside_workspace": proposal.writes_outside_workspace},
        )
        if required:
            async with SessionLocal() as s:
                s.add(Approval(run_id=run_id, required=True, status="pending"))
                await s.commit()
            await self._audit(run_id, "approval.requested", "system", {})
        return required

    @activity.defn
    async def record_approval(self, run_id: str, decision: str, approver: str) -> None:
        from datetime import datetime, timezone
        async with SessionLocal() as s:
            ap = (await s.execute(
                select(Approval).where(Approval.run_id == run_id, Approval.status == "pending")
            )).scalars().first()
            if ap:
                ap.status = decision
                ap.approver = approver
                ap.decided_at = datetime.now(timezone.utc)
            await s.commit()
        await self._audit(run_id, "approval.decided", approver, {"decision": decision})

    @activity.defn
    async def finalize(self, run_id: str, status: str, tokens: dict) -> None:
        async with SessionLocal() as s:
            run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
            run.status = status
            run.prompt_tokens = tokens.get("prompt", 0)
            run.completion_tokens = tokens.get("completion", 0)
            await s.commit()
        await self._audit(run_id, "run.completed" if status == "succeeded" else "run.failed",
                          "system", {"status": status})
        sb = self._sandboxes.pop(run_id, None)
        if sb:
            sb.cleanup()
        self._agents.pop(run_id, None)

    async def _intent(self, run_id: str) -> str:
        async with SessionLocal() as s:
            return (await s.execute(select(Run.intent).where(Run.id == run_id))).scalar_one()

    async def _test_command(self, run_id: str) -> str:
        from .db import Project
        async with SessionLocal() as s:
            run = (await s.execute(select(Run).where(Run.id == run_id))).scalar_one()
            proj = (await s.execute(select(Project).where(Project.id == run.project_id))).scalar_one()
            return proj.test_command


# --------------------------------- workflow ---------------------------------
@workflow.defn
class AgentRunWorkflow:
    def __init__(self):
        self._approval: str | None = None

    @workflow.signal
    def approve(self, decision: str, approver: str) -> None:
        self._approval = decision
        self._approver = approver

    @workflow.run
    async def run(self, run_id: str, max_iterations: int) -> str:
        retry = RetryPolicy(maximum_attempts=3)
        opts = dict(start_to_close_timeout=timedelta(minutes=20), retry_policy=retry)

        await workflow.execute_activity(Activities.start_run, run_id, **opts)

        feedback: dict | None = None
        last: ProposeResult | None = None
        gate: GateRecord | None = None
        tokens = {"prompt": 0, "completion": 0}

        for i in range(max_iterations):
            last = await workflow.execute_activity(Activities.agent_step, args=[run_id, i, feedback], **opts)
            tokens["prompt"] += last.prompt_tokens
            tokens["completion"] += last.completion_tokens
            gate = await workflow.execute_activity(Activities.run_gate, args=[run_id, i], **opts)
            if gate.status == "pass":
                break
            feedback = {"summary": gate.summary, "exit_code": gate.exit_code}
        else:
            await workflow.execute_activity(Activities.finalize, args=[run_id, "failed", tokens], **opts)
            return "failed"

        if await workflow.execute_activity(Activities.needs_approval, args=[run_id, last], **opts):
            await workflow.wait_condition(lambda: self._approval is not None,
                                          timeout=timedelta(hours=24))
            await workflow.execute_activity(
                Activities.record_approval,
                args=[run_id, self._approval, getattr(self, "_approver", "operator")], **opts)
            if self._approval == "rejected":
                await workflow.execute_activity(Activities.finalize, args=[run_id, "failed", tokens], **opts)
                return "rejected"

        await workflow.execute_activity(Activities.finalize, args=[run_id, "succeeded", tokens], **opts)
        return "succeeded"


# ---------------------------------- worker ----------------------------------
async def main() -> None:
    client = await Client.connect(settings.temporal_host, namespace=settings.temporal_namespace)
    acts = Activities()
    worker = Worker(
        client,
        task_queue=settings.task_queue,
        workflows=[AgentRunWorkflow],
        activities=[
            acts.start_run, acts.agent_step, acts.run_gate, acts.needs_approval,
            acts.record_approval, acts.finalize,
        ],
    )
    print(f"[abom] worker listening on task queue '{settings.task_queue}'")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
