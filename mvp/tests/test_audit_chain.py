"""Tamper-evidence is the certifiable core of the MVP, so it is tested first.

These tests are pure (no DB, no network) — they exercise audit.compute_hash /
make_record / verify_chain directly.
"""
from dataclasses import asdict

from abom.audit import GENESIS, make_record, verify_chain


def build_chain(events):
    """events: list of (event_type, actor, data) -> list of chain dicts."""
    chain = []
    prev = GENESIS
    for seq, (etype, actor, data) in enumerate(events):
        rec = make_record(
            run_id="run-1", seq=seq, event_type=etype, actor=actor,
            data=data, prev_hash=prev, created_at=f"2026-01-01T00:00:{seq:02d}+00:00",
        )
        chain.append(asdict(rec))
        prev = rec.hash
    return chain


SAMPLE = [
    ("run.created", "alice", {"intent": "fix login"}),
    ("model.called", "system", {"model": "local/qwen2.5-coder", "tokens": 812}),
    ("gate.evaluated", "system", {"status": "fail", "exit_code": 1}),
    ("gate.evaluated", "system", {"status": "pass", "exit_code": 0}),
    ("run.completed", "system", {"status": "succeeded"}),
]


def test_valid_chain_verifies():
    chain = build_chain(SAMPLE)
    result = verify_chain(chain)
    assert result["valid"] is True
    assert result["broken_seq"] is None


def test_mutated_payload_is_detected():
    chain = build_chain(SAMPLE)
    chain[2]["data"]["status"] = "pass"  # flip a failing gate to passing
    result = verify_chain(chain)
    assert result["valid"] is False
    assert result["broken_seq"] == 2
    assert result["reason"] == "hash mismatch"


def test_deleted_event_breaks_linkage():
    chain = build_chain(SAMPLE)
    del chain[2]                          # drop an inconvenient event
    for i, e in enumerate(chain):        # re-seq to hide the gap
        e["seq"] = i
    result = verify_chain(chain)
    assert result["valid"] is False
    assert result["reason"] in ("prev_hash mismatch", "hash mismatch")


def test_reordering_is_detected():
    chain = build_chain(SAMPLE)
    chain[2], chain[3] = chain[3], chain[2]
    result = verify_chain(chain)
    assert result["valid"] is False


if __name__ == "__main__":
    # allow running without pytest installed: python -m tests.test_audit_chain
    test_valid_chain_verifies()
    test_mutated_payload_is_detected()
    test_deleted_event_breaks_linkage()
    test_reordering_is_detected()
    print("audit chain: all checks passed")
