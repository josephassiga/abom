"""Control API: FastAPI app, auth dependency, and routes (MVP_SPEC §7)."""
from __future__ import annotations

import uuid
from typing import Annotated

from fastapi import Depends, FastAPI, Header, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .config import settings
from .db import (
    AuditEvent, Project, Run, RunStep, get_session,
)
from .schemas import (
    ApprovalDecision, AuditEventOut, ProjectCreate, ProjectOut, RunCreate,
    RunOut, StepOut, VerifyResult,
)
from . import audit

app = FastAPI(title="ABOM Control API", version="0.1.0")

Session = Annotated[AsyncSession, Depends(get_session)]


# --------------------------------- auth -------------------------------------
class Principal:
    def __init__(self, subject: str, roles: list[str]):
        self.subject = subject
        self.roles = roles


async def current_principal(authorization: str = Header(default="")) -> Principal:
    """Validate the bearer token.

    Dev mode (no OIDC_JWKS_URL): accept the static token and grant all roles.
    Phase-2: verify JWT signature against JWKS and map the `roles` claim.
    """
    token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(401, "missing bearer token")
    if not settings.oidc_jwks_url:  # dev mode
        if token != settings.dev_static_token:
            raise HTTPException(401, "invalid dev token")
        return Principal("dev@local", ["developer", "operator", "auditor"])
    # TODO: real JWKS validation
    raise HTTPException(501, "OIDC validation not implemented in MVP scaffold")


def require(role: str):
    async def dep(principal: Principal = Depends(current_principal)) -> Principal:
        if role not in principal.roles:
            raise HTTPException(403, f"role '{role}' required")
        return principal
    return dep


# --------------------------------- health -----------------------------------
@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@app.get("/readyz")
async def readyz(session: Session):
    await session.execute(select(1))
    return {"status": "ready"}


# -------------------------------- projects ----------------------------------
@app.post("/v1/projects", response_model=ProjectOut, status_code=201)
async def create_project(body: ProjectCreate, session: Session,
                         _: Principal = Depends(require("operator"))):
    proj = Project(name=body.name, repo_url=body.repo_url, test_command=body.test_command)
    session.add(proj)
    await session.commit()
    await session.refresh(proj)
    return proj


# ---------------------------------- runs ------------------------------------
@app.post("/v1/runs", response_model=RunOut, status_code=201)
async def create_run(body: RunCreate, session: Session,
                     principal: Principal = Depends(require("developer"))):
    if not (await session.execute(select(Project).where(Project.id == body.project_id))).scalar_one_or_none():
        raise HTTPException(404, "project not found")
    run = Run(project_id=body.project_id, created_by=principal.subject, intent=body.intent,
              workload_type=body.workload_type, max_iterations=body.max_iterations, status="pending")
    session.add(run)
    await session.commit()
    await session.refresh(run)
    await _start_workflow(str(run.id), body.max_iterations)
    return run


@app.get("/v1/runs/{run_id}", response_model=RunOut)
async def get_run(run_id: uuid.UUID, session: Session,
                  _: Principal = Depends(require("developer"))):
    run = (await session.execute(select(Run).where(Run.id == run_id))).scalar_one_or_none()
    if not run:
        raise HTTPException(404, "run not found")
    return run


@app.get("/v1/runs/{run_id}/steps", response_model=list[StepOut])
async def get_steps(run_id: uuid.UUID, session: Session,
                    _: Principal = Depends(require("developer"))):
    rows = (await session.execute(
        select(RunStep).where(RunStep.run_id == run_id).order_by(RunStep.seq)
    )).scalars().all()
    return rows


@app.post("/v1/runs/{run_id}/approve")
async def approve_run(run_id: uuid.UUID, body: ApprovalDecision,
                      principal: Principal = Depends(require("operator"))):
    await _signal_workflow(str(run_id), body.decision, principal.subject)
    return {"run_id": str(run_id), "decision": body.decision}


@app.post("/v1/runs/{run_id}/cancel")
async def cancel_run(run_id: uuid.UUID, _: Principal = Depends(require("operator"))):
    await _cancel_workflow(str(run_id))
    return {"run_id": str(run_id), "status": "cancelling"}


# ---------------------------------- audit -----------------------------------
@app.get("/v1/audit", response_model=list[AuditEventOut])
async def get_audit(session: Session, run_id: uuid.UUID = Query(...),
                    _: Principal = Depends(require("auditor"))):
    rows = (await session.execute(
        select(AuditEvent).where(AuditEvent.run_id == run_id).order_by(AuditEvent.seq)
    )).scalars().all()
    return rows


@app.get("/v1/audit/verify", response_model=VerifyResult)
async def verify_audit(session: Session, run_id: uuid.UUID = Query(...),
                       _: Principal = Depends(require("auditor"))):
    rows = (await session.execute(
        select(AuditEvent).where(AuditEvent.run_id == run_id).order_by(AuditEvent.seq)
    )).scalars().all()
    events = [
        {"run_id": str(r.run_id), "seq": r.seq, "event_type": r.event_type, "actor": r.actor,
         "data": r.data, "created_at": r.created_at.isoformat(),
         "prev_hash": r.prev_hash, "hash": r.hash}
        for r in rows
    ]
    result = audit.verify_chain(events)
    return VerifyResult(run_id=run_id, event_count=len(events), **result)


# ------------------------ Temporal client helpers ---------------------------
async def _client():
    from temporalio.client import Client
    return await Client.connect(settings.temporal_host, namespace=settings.temporal_namespace)


async def _start_workflow(run_id: str, max_iterations: int):
    from .orchestration import AgentRunWorkflow
    client = await _client()
    await client.start_workflow(
        AgentRunWorkflow.run, args=[run_id, max_iterations],
        id=f"run-{run_id}", task_queue=settings.task_queue,
    )


async def _signal_workflow(run_id: str, decision: str, approver: str):
    from .orchestration import AgentRunWorkflow
    client = await _client()
    handle = client.get_workflow_handle(f"run-{run_id}")
    await handle.signal(AgentRunWorkflow.approve, args=[decision, approver])


async def _cancel_workflow(run_id: str):
    client = await _client()
    await client.get_workflow_handle(f"run-{run_id}").cancel()
