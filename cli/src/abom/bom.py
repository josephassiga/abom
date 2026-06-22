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
import logging

from . import sign as _sign
from .audit import GENESIS, canonical_json, make_record, verify_chain

ABOM_VERSION = "0.1"
log = logging.getLogger("abom.bom")


def _sha256(obj) -> str:
    return hashlib.sha256(canonical_json(obj).encode("utf-8")).hexdigest()


def sign(obj: dict, key=None) -> dict:
    """Sign an ABOM object with a detached ed25519 signature."""
    return _sign.sign_obj(obj, key)


def verify_signature(obj: dict, trusted_keys=None) -> bool:
    return _sign.verify_obj(obj, trusted_keys)


# --- Composition Manifest (what the agent IS) --------------------------------
def build_composition(agent: dict, components: list[dict], controls: dict,
                      *, sign: bool = True, key=None) -> dict:
    """Build a Composition Manifest (extends CycloneDX ML-BOM), ed25519-signed by default."""
    body = {
        "abom": ABOM_VERSION, "extends": "CycloneDX ML-BOM",
        "type": "CompositionManifest",
        "agent": agent, "components": components, "controls": controls,
    }
    body["composition_sha256"] = _sha256(body)
    log.debug("composition built: %d components, sha256=%s…",
              len(components), body["composition_sha256"][:16])
    return _sign.sign_obj(body, key) if sign else body


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


def verify_abom(composition: dict, chain: list | None = None, policy: dict | None = None) -> dict:
    """Verify a Composition Manifest (+ optional Action Provenance chain) against policy.

    With no policy, checks structural integrity only (signature + chain). With a
    policy, also enforces the model allowlist, residency, egress allowlist, and
    approval coverage. Returns {"ok", "findings", "actions", "components"}.
    """
    policy = policy or {}
    chain = chain or []
    findings: list[dict] = []
    comp_hash = composition.get("composition_sha256")
    declared_models = {c.get("name") for c in composition.get("components", [])
                       if c.get("type") == "model"}
    allowed_models = policy.get("allowed_models")
    no_egress = set(policy.get("no_egress_classifications", []))
    allowed_eps = policy.get("allowed_egress_endpoints")

    if not verify_signature(composition):
        findings.append({"rule": "signature", "severity": "high",
                         "detail": "composition signature invalid or missing"})
    cv = verify_chain(chain)
    if not cv["valid"]:
        findings.append({"rule": "chain_integrity", "severity": "high",
                         "detail": f"provenance broken at seq {cv['broken_seq']} ({cv['reason']})"})

    # composition-level: declared models must be on the allowlist (when one is set)
    if allowed_models is not None:
        for nm in sorted(m for m in declared_models if m):
            if nm not in allowed_models:
                findings.append({"rule": "model_allowlist", "component": nm, "severity": "medium",
                                 "detail": f"declared model not on allowlist: {nm}"})

    for ev in chain:
        d, seq = ev["data"], ev["seq"]
        if comp_hash and d.get("composition_sha256") != comp_hash:
            findings.append({"rule": "composition_match", "seq": seq, "severity": "high",
                             "detail": "action references a different composition"})
        for mc in d.get("model_calls", []):
            m = mc.get("model")
            if allowed_models is not None and m not in allowed_models:
                findings.append({"rule": "model_allowlist", "seq": seq, "severity": "high",
                                 "detail": f"unapproved model used: {m}"})
            if m not in declared_models:
                findings.append({"rule": "composition_drift", "seq": seq, "severity": "high",
                                 "detail": f"runtime model not in signed manifest: {m}"})
        for dt in d.get("data_touched", []):
            if dt.get("egress") and dt.get("classification") in no_egress:
                findings.append({"rule": "residency", "seq": seq, "severity": "high",
                                 "detail": f"{dt.get('classification')} data egressed"})
        for ti in d.get("tools_invoked", []):
            ep = ti.get("endpoint")
            if ep and allowed_eps is not None and ep not in allowed_eps:
                findings.append({"rule": "egress_allowlist", "seq": seq, "severity": "medium",
                                 "detail": f"egress to unapproved endpoint: {ep}"})
        if any(pd.get("result") == "required" for pd in d.get("policy_decisions", [])):
            ap = d.get("approval")
            if not (ap and ap.get("decision") == "approved"):
                findings.append({"rule": "approval_coverage", "seq": seq, "severity": "high",
                                 "detail": "consequential action without approval"})

    log.info("verify: %d finding(s) over %d components / %d action(s)",
             len(findings), len(composition.get("components", [])), len(chain),
             extra={"event": "verify_done", "findings": len(findings),
                    "components": len(composition.get("components", [])), "actions": len(chain)})
    for f in findings:
        log.debug("finding: [%s] %s — %s", f.get("severity"), f.get("rule"), f.get("detail"),
                  extra={"event": "finding", "rule": f.get("rule"),
                         "severity": f.get("severity"), "detail": f.get("detail")})
    return {"ok": len(findings) == 0, "findings": findings,
            "actions": len(chain), "components": len(composition.get("components", []))}
