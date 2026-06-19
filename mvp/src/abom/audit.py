"""Tamper-evident audit log.

The hashing functions at the top are PURE (stdlib only) so they can be unit
tested without a database — see tests/test_audit_chain.py. Persistence helpers
at the bottom take an async DB session.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Iterable

GENESIS = "GENESIS"


def canonical_json(obj: Any) -> str:
    """Deterministic JSON encoding used for hashing."""
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), default=str)


def compute_hash(
    *, run_id: str, seq: int, event_type: str, actor: str, data: Any,
    prev_hash: str, created_at: str,
) -> str:
    payload = {
        "run_id": str(run_id),
        "seq": seq,
        "event_type": event_type,
        "actor": actor,
        "data": data,
        "prev_hash": prev_hash,
        "created_at": created_at,
    }
    return hashlib.sha256(canonical_json(payload).encode("utf-8")).hexdigest()


@dataclass
class AuditRecord:
    run_id: str
    seq: int
    event_type: str
    actor: str
    data: Any
    created_at: str
    prev_hash: str
    hash: str


def make_record(
    *, run_id: str, seq: int, event_type: str, actor: str, data: Any,
    prev_hash: str, created_at: str | None = None,
) -> AuditRecord:
    created_at = created_at or datetime.now(timezone.utc).isoformat()
    h = compute_hash(
        run_id=run_id, seq=seq, event_type=event_type, actor=actor,
        data=data, prev_hash=prev_hash, created_at=created_at,
    )
    return AuditRecord(run_id, seq, event_type, actor, data, created_at, prev_hash, h)


def verify_chain(events: Iterable[dict]) -> dict:
    """Recompute the chain. Returns {"valid": bool, "broken_seq": int|None, "reason": str|None}.

    `events` must be ordered by seq ascending. Each dict needs:
    run_id, seq, event_type, actor, data, created_at, prev_hash, hash.
    """
    expected_prev = GENESIS
    last_seq = None
    for e in events:
        if last_seq is not None and e["seq"] != last_seq + 1:
            return {"valid": False, "broken_seq": e["seq"], "reason": "non-contiguous seq"}
        if e["prev_hash"] != expected_prev:
            return {"valid": False, "broken_seq": e["seq"], "reason": "prev_hash mismatch"}
        recomputed = compute_hash(
            run_id=e["run_id"], seq=e["seq"], event_type=e["event_type"],
            actor=e["actor"], data=e["data"], prev_hash=e["prev_hash"],
            created_at=e["created_at"],
        )
        if recomputed != e["hash"]:
            return {"valid": False, "broken_seq": e["seq"], "reason": "hash mismatch"}
        expected_prev = e["hash"]
        last_seq = e["seq"]
    return {"valid": True, "broken_seq": None, "reason": None}


# --------------------------------------------------------------------------
# Persistence (requires DB session). Imported lazily to keep hashing pure.
# --------------------------------------------------------------------------
async def append_event(session, *, run_id: str, event_type: str, actor: str, data: Any) -> AuditRecord:
    """Append one event to a run's chain inside an existing transaction.

    Locks the run's events to compute the next seq + prev_hash atomically.
    """
    from sqlalchemy import select, func
    from .db import AuditEvent

    row = (
        await session.execute(
            select(AuditEvent)
            .where(AuditEvent.run_id == run_id)
            .order_by(AuditEvent.seq.desc())
            .limit(1)
            .with_for_update()
        )
    ).scalar_one_or_none()

    seq = (row.seq + 1) if row else 0
    prev_hash = row.hash if row else GENESIS
    rec = make_record(
        run_id=str(run_id), seq=seq, event_type=event_type, actor=actor,
        data=data, prev_hash=prev_hash,
    )
    session.add(
        AuditEvent(
            run_id=run_id, seq=rec.seq, event_type=rec.event_type, actor=rec.actor,
            data=rec.data, prev_hash=rec.prev_hash, hash=rec.hash,
            created_at=datetime.fromisoformat(rec.created_at),
        )
    )
    return rec
