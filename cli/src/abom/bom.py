"""ABOM core — Composition Manifest, Action Provenance, and abom-verify.

Pure stdlib + abom.audit for the tamper-evident chain. Two artifacts plus a
policy verifier:

  * build_composition(...)  -> signed Composition Manifest (what the agent IS)
  * append_action(...)      -> hash-chained Action Provenance (what the agent DID)
  * verify_abom(...)        -> abom-verify: policy findings over an ABOM

The signature here is an HMAC stand-in, clearly labelled. Production uses
detached ed25519 / cosign with keys in Vault/KMS — see ARCHITECTURE.md §3.6.
"""
from __future__ import annotations

import dataclasses
import hashlib
import hmac

from .audit import GENESIS, canonical_json, make_record, verify_chain

ABOM_VERSION = "0.1"
_DEMO_KEY = b"abom-cli-demo-key"  # MVP stand-in only; prod = ed25519 key in Vault/KMS


def _sha256(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def sign(obj: dict, key: bytes = _DEMO_KEY) -> dict:
    body = {k: v for k, v in obj.items() if k != "signature"}
    sig = hmac.new(key, canonical_json(body).encode("utf-8"), hashlib.sha256).hexdigest()
    return {**obj, "signature": {"alg": "hmac-sha256 (MVP; prod=ed25519)", "value": sig}}


def verify_signature(obj: dict, key: bytes = _DEMO_KEY) -> bool:
    sig = (obj.get("signature") or {}).get("value")
    if not sig:
        return False
    body = {k: v for k, v in obj.items() if k != "signature"}
    expected = hmac.new(key, canonical_json(body).encode("utf-8"), hashlib.sha256).hexdigest()
    return hmac.compare_digest(sig, expected)


# --- Composition Manifest (what the agent IS) --------------------------------
def build_composition(agent: dict, components: list[dict], controls: dict) -> dict:
    """Returns a signed Composition Manifest extending CycloneDX ML-BOM."""
    body = {
        "abom": ABOM_VERSION, "extends": "CycloneDX ML-BOM",
        "type": "CompositionManifest",
        "agent": agent, "components": components, "controls": controls,
    }
    body["composition_sha256"] = _sha256(body)
    return sign(body)


# --- Action Provenance (what the agent DID) ----------------------------------
def new_chain() -> list:
    return []


def append_action(chain: list, *, composition_sha256: str, agent_ref: str, decision: str,
                  inputs=None, model_calls=None, tools_invoked=None, data_touched=None,
                  policy_decisions=None, approval=None) -> dict:
    """Append one hash-chained Action Provenance Record to the chain."""
    data = {
        "composition_sha256": composition_sha256,
        "decision": decision,
        "inputs": inputs or [],
        "model_calls": model_calls or [],
        "tools_invoked": tools_invoked or [],
        "data_touched": data_touched or [],
        "policy_decisions": policy_decisions or [],
        "approval": approval,
    }
    prev = chain[-1]["hash"] if chain else GENESIS
    rec = make_record(run_id=agent_ref, seq=len(chain), event_type="ActionProvenance",
                      actor="abom-gen", data=data, prev_hash=prev)
    row = dataclasses.asdict(rec)
    chain.append(row)
    return row


# --- abom-verify (policy findings over an ABOM) ------------------------------
DEFAULT_POLICY = {
    "allowed_models": ["local/qwen2.5-coder"],
    "allowed_egress_endpoints": ["internal-kyc.bank"],
    "no_egress_classifications": ["confidential", "restricted"],
    "require_approval_when": "consequential",
}


def verify_abom(composition: dict, chain: list, policy: dict = DEFAULT_POLICY) -> dict:
    """Check a Composition Manifest + Action Provenance chain against policy.

    Returns {"ok": bool, "findings": [...], "actions": int}. Findings cover:
    signature, chain integrity, composition-match, model allowlist + drift,
    data residency, egress allowlist, and approval coverage.
    """
    findings: list[dict] = []
    comp_hash = composition.get("composition_sha256")
    declared_models = {c["name"] for c in composition.get("components", [])
                       if c.get("type") == "model"}

    if not verify_signature(composition):
        findings.append({"rule": "signature", "severity": "high",
                         "detail": "composition signature invalid"})
    cv = verify_chain(chain)
    if not cv["valid"]:
        findings.append({"rule": "chain_integrity", "severity": "high",
                         "detail": f"provenance broken at seq {cv['broken_seq']} ({cv['reason']})"})

    for ev in chain:
        d, seq = ev["data"], ev["seq"]
        if d.get("composition_sha256") != comp_hash:
            findings.append({"rule": "composition_match", "seq": seq, "severity": "high",
                             "detail": "action references a different composition"})
        for mc in d.get("model_calls", []):
            m = mc.get("model")
            if m not in policy["allowed_models"]:
                findings.append({"rule": "model_allowlist", "seq": seq, "severity": "high",
                                 "detail": f"unapproved model used: {m}"})
            if m not in declared_models:
                findings.append({"rule": "composition_drift", "seq": seq, "severity": "high",
                                 "detail": f"runtime model not in signed manifest: {m}"})
        for dt in d.get("data_touched", []):
            if dt.get("egress") and dt.get("classification") in policy["no_egress_classifications"]:
                findings.append({"rule": "residency", "seq": seq, "severity": "high",
                                 "detail": f"{dt.get('classification')} data egressed"})
        for ti in d.get("tools_invoked", []):
            ep = ti.get("endpoint")
            if ep and ep not in policy["allowed_egress_endpoints"]:
                findings.append({"rule": "egress_allowlist", "seq": seq, "severity": "medium",
                                 "detail": f"egress to unapproved endpoint: {ep}"})
        if any(pd.get("result") == "required" for pd in d.get("policy_decisions", [])):
            ap = d.get("approval")
            if not (ap and ap.get("decision") == "approved"):
                findings.append({"rule": "approval_coverage", "seq": seq, "severity": "high",
                                 "detail": "consequential action without approval"})

    return {"ok": len(findings) == 0, "findings": findings, "actions": len(chain)}
