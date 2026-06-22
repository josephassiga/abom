# ABOM Specification — v0.1

The **Agent Bill of Materials (ABOM)** is a signed, standard, tamper-evident
record of what an AI agent **is** and what it **did**. It extends the
[CycloneDX ML-BOM](https://cyclonedx.org/capabilities/mlbom/) concept from models
to full agentic systems and adds *runtime provenance*.

> Status: **draft v0.1**. The format is pre-1.0 and may change; breaking changes
> bump the version (`abom-0.2`, …) and are never silent. See
> [../GOVERNANCE.md](../GOVERNANCE.md).

- Machine-readable schema: [`abom-0.1.schema.json`](abom-0.1.schema.json)
- Examples: [`examples/`](examples/)

## Two artifacts

| Artifact | Answers | When |
|---|---|---|
| **Composition Manifest** | *What is this agent made of?* | At build / deploy |
| **Action Provenance Record** | *What did this agent do?* | Per consequential action (runtime) |

They are linked: every Action Provenance Record carries the
`composition_sha256` of the manifest it ran under.

## 1. Composition Manifest

A signed inventory of everything an agent is built from.

```json
{
  "abom": "0.1",
  "extends": "CycloneDX ML-BOM",
  "type": "CompositionManifest",
  "agent": { "name": "loan-doc-agent", "version": "1.4.0", "risk_class": "high (Annex III)" },
  "components": [
    { "type": "model", "name": "local/qwen2.5-coder", "weights_sha256": "…", "egress": false },
    { "type": "tool", "name": "http_fetch", "scope": "egress", "allowed_endpoints": ["internal-kyc.bank"] },
    { "type": "prompt", "role": "system", "sha256": "…" },
    { "type": "dataSource", "name": "core_banking_repo", "classification": "confidential" },
    { "type": "policy", "engine": "OPA", "sha256": "…" }
  ],
  "controls": { "egress": "deny-by-default", "hitl": "required-for-consequential", "residency": "EU" },
  "composition_sha256": "…",
  "signature": { "alg": "ed25519", "value": "…" }
}
```

**Component types:** `model` · `tool` · `prompt` · `dataSource` · `policy` ·
`framework` · `mcpServer`. Each carries a `name` and type-specific fields (e.g.
`weights_sha256` for a model, `allowed_endpoints` for an egress tool,
`classification` for a data source).

`composition_sha256` is the SHA-256 of the canonical manifest (excluding the
signature) and is the **join key** used by provenance records and by
composition-drift checks.

## 2. Action Provenance Record

One record per consequential action, hash-chained for tamper-evidence.

```json
{
  "run_id": "loan-doc-agent@1.4.0",
  "seq": 1,
  "event_type": "ActionProvenance",
  "actor": "abom-gen",
  "data": {
    "composition_sha256": "…",
    "decision": "submit memo for disbursement",
    "inputs": [{ "kind": "retrieved", "source": "core_banking_repo" }],
    "model_calls": [{ "model": "local/qwen2.5-coder", "tokens": 812 }],
    "tools_invoked": [{ "name": "http_fetch", "endpoint": "internal-kyc.bank" }],
    "data_touched": [{ "classification": "confidential", "egress": false }],
    "policy_decisions": [{ "rule": "approval_required", "result": "required" }],
    "approval": { "by": "operator@bank", "decision": "approved" }
  },
  "prev_hash": "…",
  "hash": "…"
}
```

## 3. Signing

Composition Manifests are signed; the `signature` object carries `alg` and
`value`. The reference implementation ships an HMAC stand-in (clearly labelled);
**production deployments use detached ed25519 / Sigstore** with keys in a
KMS/Vault.

## 4. Tamper-evidence (the hash chain)

Action Provenance Records form a per-run hash chain:

```
hash = SHA256( canonical_json({
  run_id, seq, event_type, actor, data, prev_hash, created_at
}) )
```

- `canonical_json` = `json.dumps(obj, sort_keys=True, separators=(",",":"), default=str)`
- the first record uses `prev_hash = "GENESIS"`
- `seq` is dense and monotonic per run

Any mutation, insertion, deletion, or reordering breaks the chain — verification
recomputes every hash and reports the first broken `seq`.

## 5. Verification (`abom-verify`)

A conforming verifier checks, at minimum:

| Check | Fails when |
|---|---|
| `signature` | the manifest signature is invalid |
| `chain_integrity` | the provenance chain has been tampered with |
| `composition_match` | an action references a different composition |
| `model_allowlist` | a model not on the approved list was used |
| `composition_drift` | a runtime model is not in the signed manifest (shadow model) |
| `residency` | confidential/restricted data was egressed |
| `egress_allowlist` | egress to an unapproved endpoint occurred |
| `approval_coverage` | a consequential action has no approval |

## 6. Relationship to CycloneDX

ABOM **extends** CycloneDX ML-BOM rather than replacing it: a Composition Manifest
maps to a CycloneDX BOM whose `components` include models (ML-BOM), tools, prompts,
data sources, and policies. The Action Provenance Record is the new, agent-specific
runtime layer. Where a field has a CycloneDX equivalent, ABOM aligns with it.

## Versioning

The spec version is the `abom` field (`"0.1"`). Additive changes keep the version;
breaking changes increment it and ship a new schema file alongside the old one.
