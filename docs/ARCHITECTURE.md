# ABOM — Architecture Solution

**The Agent Bill of Materials: generate · sign · verify · notarize — for any agent, on any Kubernetes, inside the customer's boundary.**

*Companion to [STRATEGY.md](STRATEGY.md) v3.0. This is the technical solution: components, data flow, the schema, and the trade-offs behind each.*

---

## 1. Requirements

### Functional
- **Generate** two artifacts for any agent: a **Composition Manifest** (static — models, tools, prompts, data sources, policies, controls) and **Action Provenance Records** (runtime — per consequential action).
- **Sign** every artifact (detached, verifiable) and **hash-chain** the runtime records so tampering is detectable.
- **Verify** an ABOM against policy: model allowlist, egress/PII rules, approval coverage, and *composition-match* (the deployed agent equals its signed manifest).
- **Notarize**: an append-only, queryable registry that is the system of record, with **SIEM and CycloneDX exports** for auditors and regulators.
- **Capture completely** from inside the agent runtime / control plane so no model call, tool call, or data access is missed.
- Be **standard-first**: ABOM v0.1 extends **CycloneDX ML-BOM**.

### Non-functional
| Property | Target |
|---|---|
| **Sovereignty** | Runs in the customer boundary; nothing leaves without explicit, logged policy. Air-gap capable. |
| **Tamper-evidence** | Hash-chained + signed; any mutation/insertion/deletion/reorder is detectable to the exact record. |
| **Completeness** | Generated where every agent action is observable — runtime/control-plane position. |
| **Neutrality** | Any model, any framework, any cloud. We sign artifacts; we don't run the agent's models. |
| **Portability** | CNCF-native; any Kubernetes, on-prem or air-gapped. |

### Constraints
- Small team → **extend an open standard (CycloneDX), open-source the generator**, own verification + the notary.
- Must integrate with heterogeneous agent runtimes (LangGraph, CrewAI, MCP servers, custom) without owning them.

---

## 2. High-level design

```
                       CUSTOMER TRUST BOUNDARY (their Kubernetes)
┌───────────────────────────────────────────────────────────────────────────┐
│  AGENT RUNTIME (any framework)                                              │
│     model calls · tool calls · data access · policy decisions · approvals   │
│        │                                                                    │
│        ▼   instrumentation hooks / sidecar / control-plane taps            │
│  ┌──────────── abom-gen ────────────┐                                       │
│  │ collectors → Composition Manifest │  (at deploy)                         │
│  │ collectors → Action Provenance    │  (per consequential action)          │
│  │ canonicalize · hash-chain · SIGN  │                                       │
│  └───────────────┬───────────────────┘                                      │
│                  ▼                                                           │
│  ┌──────────── THE NOTARY (registry) ───────────┐    ┌─ abom-verify ─────┐  │
│  │ append-only · hash-chained · signed           │◄──►│ policy engine (OPA)│  │
│  │ queryable (Postgres + index) · WORM option    │    │ composition-match  │  │
│  │ exports: SIEM · CycloneDX                      │    │ → signed attestation│ │
│  └───────────────────────────────────────────────┘    └────────────────────┘ │
│                  ▲ keys in Vault/KMS · ed25519 / cosign                      │
└───────────────────────────────────────────────────────────────────────────┘
        ▲ optional, consent-gated mirror to a shared Notary (off in air-gap)
```

### Components

| Component | Build / Source / Own | Technology |
|---|---|---|
| **ABOM schema (the standard)** | **Own (open)** | JSON Schema extending CycloneDX ML-BOM |
| **abom-gen** (collectors, canonicalize, hash-chain, sign) | **Own (open-source)** | Python SDK + runtime hooks / sidecar; ed25519 (cosign-compatible) |
| Framework/runtime adapters | Source + wrap | LangGraph / CrewAI / MCP / OpenAI-SDK taps; model-router + tool-gateway taps |
| **abom-verify** | **Own (paid)** | OPA/Rego (MVP: JSON policy) → signed verification attestation |
| **The Notary** (registry) | **Own (paid)** | Postgres (append-only, hash-chained) + OpenSearch index; MinIO/WORM for archival |
| Key management | Integrate | HashiCorp Vault / KMS |
| Exporters | Build | SIEM (CEF/JSON), CycloneDX |
| Platform / infra | Source | Kubernetes, Operator + Helm, OpenTelemetry |

Owned = the standard, verification, and the notary (the trust). Sourced = adapters, datastores, platform.

---

## 3. Deep dives

### 3.1 The schema (ABOM v0.1)
Two object types, both extending CycloneDX ML-BOM:
- **Composition Manifest** — `agent` metadata + `components[]` (model / tool / prompt / dataSource / policy / framework / mcpServer) + `controls` + `signature`. Its `composition_sha256` is the join key.
- **Action Provenance Record** — `agent_ref` (→ composition hash), `seq`, `decision`, `inputs[]`, `model_calls[]`, `tools_invoked[]`, `data_touched[]`, `policy_decisions[]`, `approval`, `prev_hash`, `hash`.

### 3.2 abom-gen — capture & coverage (the hard part)
Completeness is the whole game. Three capture modes, in order of fidelity:
1. **Control-plane taps** — when the agent runs through our model router + tool gateway, every model/tool call is observed natively (highest fidelity).
2. **Runtime hooks** — an SDK that instruments popular frameworks (callbacks/middleware) and MCP servers.
3. **Sidecar/eBPF egress watch** — a network-level backstop that records any egress the higher layers missed, so the ABOM can *assert* "no unobserved egress."
Each captured action is canonicalized, hash-chained to the previous (`prev_hash`), and signed before it leaves memory.

### 3.3 Tamper-evidence
`hash = SHA256(canonical_json({agent_ref, seq, decision, …, prev_hash, created_at}))`; first record uses `prev_hash = "GENESIS"`; `unique(agent_ref, seq)`. `verify_chain()` recomputes every hash and returns the first broken `seq`. Phase-2: periodic anchoring + WORM copy. (This is the chain already shipped in the MVP.)

### 3.4 abom-verify — the policy checks
Decidable properties over the ABOM:
- **Model allowlist** — every `model` component is approved.
- **Egress / residency** — no `data_touched` of class *X* leaves; only `allowed_endpoints` are used.
- **Approval coverage** — every consequential action carries a valid `approval`.
- **Composition-match** — the deployed agent's measured composition hash equals the signed manifest (no drift, no swapped model).
Output: a pass/fail result with findings, emitted as a **signed verification attestation** that itself enters the Notary.

### 3.5 The Notary
Append-only, signed, hash-chained store of all manifests, provenance records, and verification attestations; indexed for query ("show every action the loan agent took on confidential data last quarter"); exportable to SIEM and as CycloneDX. Its value is third-party independence — which is why it is the monetizable, can't-self-host asset even though abom-gen is open.

### 3.6 Trust & keys
Signing keys live in Vault/KMS; the Notary holds the independent signer. Verifiers (auditors, regulators) check signatures against published public keys — trust is in the keys + the chain, not in our word.

---

## 4. Deployment

A self-contained stack installed into the customer's Kubernetes — private cloud, on-prem, or air-gapped — via Operator + Helm. abom-gen runs as an SDK/sidecar next to agents; the Notary and abom-verify run in-cluster. An optional, consent-gated mirror to a shared/managed Notary is available and is fully disabled in air-gap mode.

---

## 5. Trade-offs (explicit)

| Decision | Chosen | Alternative | Why |
|---|---|---|---|
| Standard | Extend CycloneDX ML-BOM | Invent a new format | Ride the winner; avoid an adoption fight you'll lose |
| Open vs. paid | Open-source gen + schema; paid verify + notary | Close everything | Adoption wins the standard; trust (notary) is the moat |
| Capture | Control-plane taps + SDK hooks + eBPF backstop | SDK only | SDK alone misses calls; the backstop lets you *assert* completeness |
| Tamper-evidence | Hash chain + sign + WORM | Blockchain | Same guarantee, far simpler, explainable to auditors |
| Policy engine | OPA/Rego (MVP: JSON) | Bespoke | Mature, auditable, ecosystem |
| Deployment | In-boundary, air-gap capable | SaaS-only | Sovereignty is non-negotiable for the wedge |

---

## 6. What to revisit as it grows
- **eBPF/TEE-rooted capture** for hard completeness guarantees and hardware-attested provenance.
- **Cross-org Notary federation** + a public transparency log (Certificate-Transparency-style) for the standard.
- **Proof-Carrying Actions** — escalate verify-after from attestation to *gate-before* (admission control that rejects any action without a valid proof). The ABOM is the on-ramp.

---

## 7. Phased build (maps to the MVP)

1. **ABOM v0 + abom-gen v0** — instrument one agent run; emit a signed Composition Manifest + hash-chained Action Provenance chain. *(MVP)*
2. **abom-verify v0** — one decidable check (e.g., unapproved-model or confidential-data-to-egress) that catches a real violation a naked agent would hide.
3. **The Notary v0** — append-only registry + verify-on-write + CycloneDX/SIEM export.
4. **Coverage** — framework adapters + eBPF egress backstop to assert completeness.
5. **Hardening** — air-gap bundle, WORM, anchoring, multi-tenancy.

*Step 1–2 is the lighthouse deliverable; the tamper-evident chain from the existing demo is step 0.*
