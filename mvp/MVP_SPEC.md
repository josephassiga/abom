# ABOM — Step-1 MVP Specification

*Build target for the lighthouse design partner. Detailed enough to scaffold from. Companion to the project docs (kept private) §7 and the project docs (kept private).*

---

## 1. Goal

For **one real agent run, entirely inside the customer's boundary**, produce a
signed **Agent Bill of Materials** and verify it:

1. **Generate** — a signed **Composition Manifest** (what the agent is made of) and
   a hash-chained **Action Provenance** chain (what it did).
2. **Verify** — run **abom-verify** against policy and catch a real violation a raw
   log would let ship silently (unapproved/shadow model, confidential-data egress,
   missing approval, composition drift).
3. **Prove** — show the provenance is tamper-evident: scrubbing a record breaks the
   chain at the exact `seq`.

Guiding constraint: *nothing leaves the boundary*. The ABOM format extends
**CycloneDX ML-BOM**.

---

## 2. The workload

An agent run (the MVP exercises a developer/document agent) whose actions —
model calls, tool/egress calls, data access, gate results, approvals — are
captured as Action Provenance and bound to a signed Composition Manifest.

### Out of scope for MVP
Full runtime auto-capture (eBPF/framework taps) · real ed25519/cosign signing
(MVP uses an HMAC stand-in) · the persistent Notary registry · OPA/Rego (MVP uses
a JSON policy) · web console · multi-tenancy · SIEM export · air-gap bundle.

---

## 3. The ABOM artifacts (the core)

**Composition Manifest** — signed; `composition_sha256` is the join key.
```json
{ "abom":"0.1","extends":"CycloneDX ML-BOM","type":"CompositionManifest",
  "agent":{"name":"…","version":"…","risk_class":"high (Annex III)"},
  "components":[ {"type":"model","name":"…","weights_sha256":"…","egress":false},
                 {"type":"tool","name":"http_fetch","allowed_endpoints":["…"]},
                 {"type":"prompt","sha256":"…"},
                 {"type":"dataSource","classification":"confidential"},
                 {"type":"policy","engine":"OPA","sha256":"…"} ],
  "controls":{"egress":"deny-by-default","hitl":"required-for-consequential","residency":"EU"},
  "composition_sha256":"…","signature":{"alg":"…","value":"…"} }
```

**Action Provenance Record** — hash-chained (reuses the audit chain).
```json
{ "type":"ActionProvenance","run_id":"agent@ver","seq":1,
  "data":{ "composition_sha256":"…","decision":"…",
           "inputs":[…],"model_calls":[{"model":"…","tokens":…}],
           "tools_invoked":[{"name":"…","endpoint":"…"}],
           "data_touched":[{"classification":"confidential","egress":false}],
           "policy_decisions":[{"rule":"approval_required","result":"required"}],
           "approval":{"by":"…","decision":"approved"} },
  "prev_hash":"…","hash":"…" }
```

Implemented in [src/abom/bom.py](src/abom/bom.py) (`build_composition`,
`append_action`, `sign`/`verify_signature`) over the tamper-evident chain in
[src/abom/audit.py](src/abom/audit.py).

---

## 4. abom-verify — policy checks

`bom.verify_abom(composition, chain, policy)` → `{ok, findings[], actions}`. Rules:

| Rule | Catches |
|---|---|
| `signature` | composition signature invalid |
| `chain_integrity` | provenance mutated / scrubbed / reordered |
| `composition_match` | an action references a different composition |
| `model_allowlist` | a model not on the approved list was used |
| `composition_drift` | a runtime model not in the signed manifest (shadow model) |
| `residency` | confidential/restricted data egressed |
| `egress_allowlist` | egress to an unapproved endpoint |
| `approval_coverage` | a consequential action without approval |

Phase-2 swaps the JSON policy for OPA/Rego behind the same interface.

---

## 5. Tech stack & substrate

Where ABOMs are captured: the agent runs through the control-plane substrate so
every action is observable. (Capture completeness is the product's hardest
property — see the project docs (kept private) §3.2.)

| Concern | Choice |
|---|---|
| Language | Python 3.12 |
| API | FastAPI + Pydantic v2 |
| Orchestration | Temporal (`temporalio`) |
| DB / ORM | PostgreSQL 16 + SQLAlchemy 2.0 (async) |
| Object store | MinIO (S3) |
| Model serving | vLLM (OpenAI-compatible); `MockModelClient` for laptops |
| Policy | JSON (MVP) → OPA/Rego |
| Signing | HMAC stand-in (MVP) → ed25519 / cosign |
| Deploy | Helm stub (`charts/abom`), any Kubernetes |

---

## 6. API surface (MVP)

Bearer token; `roles` claim drives RBAC (`developer`, `operator`, `auditor`).

| Method | Path | Role | Purpose |
|---|---|---|---|
| GET | `/healthz` `/readyz` | — | liveness / readiness |
| POST | `/v1/runs` | developer | start an instrumented agent run |
| GET | `/v1/runs/{id}/abom` | auditor | the run's Composition Manifest + Action Provenance |
| GET | `/v1/abom/verify?run_id=` | auditor | run abom-verify → findings |
| GET | `/v1/abom/chain/verify?run_id=` | auditor | recompute the provenance hash chain |
| POST | `/v1/runs/{id}/approve` | operator | approve a consequential action |

---

## 7. Definition of done

1. A run completes against a **local** model only — zero external egress, verifiable.
2. The run emits a **signed Composition Manifest** and a **hash-chained Action Provenance** chain.
3. **abom-verify** returns **clean** for a compliant run and **≥3 findings** for a violating run (shadow model + confidential egress + missing approval).
4. Tampering with any provenance record makes `verify_abom` report a `chain_integrity` finding at the broken `seq`.
5. RBAC enforced: `auditor` cannot start runs; `developer` cannot approve.
6. `make demo` runs the generate → verify → tamper scenario with no infrastructure.

The demo ([demo/demo.py](demo/demo.py)) already satisfies criteria 2–4 and 6.

---

## 8. Milestones (≈6 weeks, one engineer)

| Wk | Deliverable |
|---|---|
| 1 | ABOM v0 schema + `bom.py` (composition, provenance, verify) + tamper test ✓ |
| 2 | Control API: runs, `/v1/runs/{id}/abom`, `/v1/abom/verify`, RBAC |
| 3 | Capture hooks in the model router + tool gateway (real model/tool/data events) |
| 4 | Real ed25519/cosign signing; persist to a minimal Notary (append-only table) |
| 5 | CycloneDX + SIEM export; second decidable verify rule hardened |
| 6 | docker-compose end-to-end; Helm stub; design-partner demo |

---

## 9. Risk specific to the MVP

**Capture completeness.** A provenance chain is only trustworthy if *every* action
is recorded. The MVP supplies actions explicitly; the product earns completeness
by generating from inside the runtime (control-plane taps + framework hooks + an
eBPF egress backstop). Keep the `abom-gen` capture interface stable so those
sources can be added without changing the artifacts.
