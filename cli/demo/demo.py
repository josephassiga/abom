"""ABOM demo — generate · verify · prove tamper-evidence.

Runs an agent two ways and shows what ABOM does that raw logs don't:

  * COMPLIANT run  — approved model, no bad egress, consequential action approved.
  * VIOLATING run  — a shadow (unapproved) model call, confidential data egressed
                     to an unapproved endpoint, and a consequential action with no
                     approval — exactly the things that ship silently without ABOM.

For each run we emit a signed **Composition Manifest** and a hash-chained
**Action Provenance** chain, then run **abom-verify**. The compliant run verifies
clean; the violating run is blocked with provable findings. Finally we show that
quietly scrubbing the evidence breaks the chain.

The agent's test gate is a real subprocess (sample_repo/tests.py). The model is a
deterministic mock — what this demo proves is ABOM (composition + provenance +
verify + tamper-evidence), not model quality.

Run:  python3 demo/demo.py        (from the cli/ directory)
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "src"))

from abom import bom  # noqa: E402

SAMPLE_REPO = os.path.join(HERE, "sample_repo")
OUT = os.path.join(HERE, "out")

FIXED = '''def validate_login(username, password):
    if not isinstance(username, str) or not isinstance(password, str):
        return False
    if not username.strip() or not password.strip():
        return False
    return True
'''


# --- a real gate run (real subprocess, real exit code) -----------------------
def run_gate() -> tuple[bool, str]:
    ws = tempfile.mkdtemp(prefix="abom-demo-")
    try:
        for fn in os.listdir(SAMPLE_REPO):
            shutil.copy(os.path.join(SAMPLE_REPO, fn), os.path.join(ws, fn))
        with open(os.path.join(ws, "validator.py"), "w") as fh:
            fh.write(FIXED)
        p = subprocess.run([sys.executable, "tests.py"], cwd=ws,
                           capture_output=True, text=True, timeout=30)
        return p.returncode == 0, (p.stdout + p.stderr).strip().splitlines()[0]
    finally:
        shutil.rmtree(ws, ignore_errors=True)


# --- the shared Composition Manifest (what the agent IS) ---------------------
def build_manifest() -> dict:
    return bom.build_composition(
        agent={"name": "loan-doc-agent", "version": "1.4.0", "risk_class": "high (Annex III)"},
        components=[
            {"type": "model", "name": "local/qwen2.5-coder", "weights_sha256": "abc123",
             "provenance": "local/vLLM", "egress": False},
            {"type": "tool", "name": "http_fetch", "scope": "egress",
             "allowed_endpoints": ["internal-kyc.bank"]},
            {"type": "prompt", "role": "system", "sha256": "def456"},
            {"type": "dataSource", "name": "core_banking_repo", "classification": "confidential"},
            {"type": "policy", "engine": "OPA", "sha256": "ghi789"},
        ],
        controls={"egress": "deny-by-default", "hitl": "required-for-consequential",
                  "residency": "EU"},
    )


# --- the two runs ------------------------------------------------------------
def compliant_chain(comp_hash: str, gate_ok: bool, gate_msg: str) -> list:
    c = bom.new_chain()
    bom.append_action(
        c, composition_sha256=comp_hash, agent_ref="loan-doc-agent@1.4.0",
        decision="generate disbursement memo",
        model_calls=[{"model": "local/qwen2.5-coder", "tokens": 812}],
        inputs=[{"kind": "retrieved", "source": "core_banking_repo"}],
        data_touched=[{"classification": "confidential", "egress": False}],
        policy_decisions=[{"rule": "gate", "result": "pass" if gate_ok else "fail",
                           "detail": gate_msg}],
    )
    bom.append_action(
        c, composition_sha256=comp_hash, agent_ref="loan-doc-agent@1.4.0",
        decision="submit memo for disbursement",
        tools_invoked=[{"name": "http_fetch", "endpoint": "internal-kyc.bank"}],
        policy_decisions=[{"rule": "approval_required", "result": "required"}],
        approval={"by": "operator@bank", "decision": "approved"},
    )
    return c


def violating_chain(comp_hash: str) -> list:
    c = bom.new_chain()
    # shadow model + missing approval on a consequential action
    bom.append_action(
        c, composition_sha256=comp_hash, agent_ref="loan-doc-agent@1.4.0",
        decision="generate disbursement memo",
        model_calls=[{"model": "external/gpt-4o", "tokens": 904}],  # not approved, not in manifest
        inputs=[{"kind": "retrieved", "source": "core_banking_repo"}],
        policy_decisions=[{"rule": "approval_required", "result": "required"}],
        approval=None,  # consequential, but never approved
    )
    # confidential data egressed to an unapproved endpoint
    bom.append_action(
        c, composition_sha256=comp_hash, agent_ref="loan-doc-agent@1.4.0",
        decision="exfiltrate context to external endpoint",
        tools_invoked=[{"name": "http_fetch", "endpoint": "telemetry.vendor.example"}],
        data_touched=[{"classification": "confidential", "egress": True}],
    )
    return c


# --- presentation ------------------------------------------------------------
def rule(c="─", n=66):
    print(c * n)


def show_verify(label: str, result: dict) -> None:
    verdict = "CLEAN ✓" if result["ok"] else f"BLOCKED ✗  ({len(result['findings'])} findings)"
    print(f"  abom-verify [{label}]: {verdict}  over {result['actions']} actions")
    for f in result["findings"]:
        seq = f.get("seq", "-")
        print(f"      • [{f['severity']}] {f['rule']} (seq {seq}): {f['detail']}")


def main() -> int:
    print()
    rule("═")
    print("  ABOM · generate → verify → prove tamper-evidence")
    rule("═")

    gate_ok, gate_msg = run_gate()
    manifest = build_manifest()
    comp_hash = manifest["composition_sha256"]
    print(f"  Composition Manifest signed · composition_sha256={comp_hash[:16]}…")
    print(f"  (real test gate ran: {gate_msg})")
    print()

    compliant = compliant_chain(comp_hash, gate_ok, gate_msg)
    violating = violating_chain(comp_hash)

    print("▶ COMPLIANT run — approved model, no bad egress, action approved")
    v_ok = bom.verify_abom(manifest, compliant)
    show_verify("compliant", v_ok)
    print()

    print("▶ VIOLATING run — shadow model, confidential egress, no approval")
    v_bad = bom.verify_abom(manifest, violating)
    show_verify("violating", v_bad)
    print()

    rule()
    print("  Without ABOM, the violating run ships silently.")
    print("  With ABOM, every violation is caught — and provable.")
    rule()
    print()

    # tamper: quietly scrub the egress evidence
    print("▶ TAMPER — hide the egress by editing the provenance record")
    tampered = json.loads(json.dumps(violating))
    tampered[1]["data"]["data_touched"] = []          # erase the confidential egress
    tampered[1]["data"]["decision"] = "submit memo"   # relabel the action
    v_tampered = bom.verify_abom(manifest, tampered)
    broke = any(f["rule"] == "chain_integrity" for f in v_tampered["findings"])
    print(f"  scrubbing the record → chain integrity: "
          f"{'BROKEN (detected)' if broke else 'intact (!?)'}")
    print()

    os.makedirs(OUT, exist_ok=True)
    json.dump(manifest, open(os.path.join(OUT, "composition.json"), "w"), indent=2)
    json.dump(compliant, open(os.path.join(OUT, "provenance_compliant.json"), "w"), indent=2)
    json.dump(violating, open(os.path.join(OUT, "provenance_violating.json"), "w"), indent=2)
    json.dump({"compliant": v_ok, "violating": v_bad,
               "tamper_detected": broke},
              open(os.path.join(OUT, "verify.json"), "w"), indent=2)
    print(f"  Artifacts written to {os.path.relpath(OUT)}/ "
          "(composition + provenance chains + verify.json)")
    print()

    ok = v_ok["ok"] and (not v_bad["ok"]) and len(v_bad["findings"]) >= 3 and broke
    print("✓ DEMO ASSERTIONS PASSED" if ok else "✗ DEMO ASSERTIONS FAILED")
    rule("═")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
