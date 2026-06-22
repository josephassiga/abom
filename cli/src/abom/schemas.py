"""Pydantic request/response models for the Control API."""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field


class ProjectCreate(BaseModel):
    name: str
    repo_url: str
    test_command: str = "pytest -q"


class ProjectOut(BaseModel):
    id: uuid.UUID
    name: str
    repo_url: str
    test_command: str

    model_config = {"from_attributes": True}


class RunCreate(BaseModel):
    project_id: uuid.UUID
    intent: str = Field(min_length=3)
    workload_type: Literal["dev_agent"] = "dev_agent"
    max_iterations: int = Field(default=4, ge=1, le=8)


class RunOut(BaseModel):
    id: uuid.UUID
    project_id: uuid.UUID
    intent: str
    status: str
    model: str
    max_iterations: int
    prompt_tokens: int
    completion_tokens: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StepOut(BaseModel):
    seq: int
    type: str
    payload: dict[str, Any]
    created_at: datetime

    model_config = {"from_attributes": True}


class ApprovalDecision(BaseModel):
    decision: Literal["approved", "rejected"]
    comment: str = ""


class AuditEventOut(BaseModel):
    seq: int
    event_type: str
    actor: str
    data: dict[str, Any]
    prev_hash: str
    hash: str
    created_at: datetime

    model_config = {"from_attributes": True}


class VerifyResult(BaseModel):
    run_id: uuid.UUID
    valid: bool
    broken_seq: int | None = None
    reason: str | None = None
    event_count: int
