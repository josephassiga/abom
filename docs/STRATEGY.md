# ABOM — The Agent Bill of Materials

**Founding strategy · v3.0**
*A signed, standard, tamper-evident record of what every AI agent is — and what it did.*

> Company: **ABOM** · **abom.ai**
> CONFIDENTIAL — for internal use in company formation

---

## 0. What changed (v2 → v3)

v2 framed the company as a *production control plane* for agentic AI — own the reliability runtime, govern agent fleets. Strong, but it competed in a crowded, capability-led race and made trust depend on a vendor's reputation. v3 makes a sharper, more defensible bet on the layer underneath every agent: **accountability.**

The pivot: stop trying to make the agent better or more trusted. **Make the agent *legible and attestable*** — produce a signed, standard record of exactly what each agent is composed of and every consequential thing it did. SBOMs did this for software supply chains and then became mandated. Agents are next. ABOM is that primitive — and whoever defines it becomes infrastructure.

The reliability/audit machinery from v2 isn't discarded: the tamper-evident chain we already built *is* the runtime substrate of an ABOM. We're re-centering on the artifact, the standard, and the neutral notary around it.

---

## 1. Executive summary

Agentic AI is moving into production inside regulated institutions, and a question no one can answer well today is about to become a compliance requirement: **"What is this agent made of, and what exactly did it do?"** Risk officers, auditors, and regulators need a verifiable account of every model, tool, prompt, data source, and policy an agent used — and of every consequential decision it took. They have logs they must trust; they do not have a *signed, standard, tamper-evident bill of materials*.

**ABOM is the Agent Bill of Materials**: a standard format plus the tooling to generate, verify, and notarize it. Two artifacts:

- **Composition Manifest** — the ingredients label: every model (with weight hashes), tool, prompt, data source, framework, and policy that makes up an agent. Signed at deploy time.
- **Action Provenance Record** — the flight recorder: for each consequential action, the inputs, model calls, tools invoked, data classification, policy decisions, and approvals — hash-chained and tamper-evident, linked back to the composition.

Around that standard sit three products: **abom-gen** (open-source generator/SDK that auto-emits ABOMs), **abom-verify** (checks an ABOM against policy — the part risk teams pay for), and **the Notary** (a signed, queryable registry — the neutral system of record auditors and regulators query). We open-source the format and the generator to win the standard, and monetize verification and the notary.

We extend the emerging **CycloneDX ML-BOM** standard to full agents and runtime provenance rather than forking it. We land in **European regulated financial services**, ~12–18 months ahead of a mandate the SBOM precedent makes nearly inevitable. Underneath the software, this is a trust company — and the trust is *cryptographic*, not reputational.

---

## 2. The problem

Agents are becoming autonomous black boxes inside institutions that are legally accountable for what software does. Three gaps:

- **Composition is opaque.** No one can say, in one signed document, which models/tools/prompts/data/policies an agent is actually built from — or prove the deployed agent matches what was approved.
- **Actions are unaccountable.** When an agent makes a consequential decision, the evidence is scattered application logs the institution must *trust* — not a tamper-evident, portable record it can *verify* and hand to a regulator.
- **The mandate is coming and no one is ready.** AI Act Art. 12 (record-keeping), DORA (evidence of ICT control), and NIST AI RMF all point at "account for what your AI is and did." SBOM went from optional to mandated in three years; agent accountability is on the same trajectory, and the tooling doesn't exist.

The market is racing to make agents *do more*. Almost no one is building the layer that makes an agent *answerable*. That is the gap.

---

## 3. The product

### 3.1 The two artifacts

**Composition Manifest** (static — what the agent *is*):
```json
{ "abom": "0.1", "extends": "CycloneDX ML-BOM",
  "agent": {"name":"loan-doc-agent","version":"1.4.0","risk_class":"high (Annex III)"},
  "components": [
    {"type":"model","name":"qwen2.5-coder","weights_sha256":"…","provenance":"local/vLLM","egress":false},
    {"type":"tool","name":"http_fetch","scope":"egress","allowed_endpoints":["internal-kyc.bank"]},
    {"type":"prompt","role":"system","sha256":"…"},
    {"type":"dataSource","name":"core_banking_repo","classification":"confidential"},
    {"type":"policy","engine":"OPA","sha256":"…"} ],
  "controls": {"egress":"deny-by-default","hitl":"required-for-consequential","residency":"EU"},
  "signature": {"alg":"ed25519","signer":"abom-notary","value":"…"} }
```

**Action Provenance Record** (runtime — what the agent *did*, per consequential action):
```json
{ "abom":"0.1","type":"ActionProvenance",
  "agent_ref":"loan-doc-agent@1.4.0 (composition_sha256=…)",
  "run_id":"…","seq":42,"decision":"approved disbursement memo",
  "inputs":[{"kind":"retrieved","source":"core_banking_repo","sha256":"…"}],
  "model_calls":[{"model":"qwen2.5-coder","tokens":812,"output_sha256":"…"}],
  "tools_invoked":[{"name":"http_fetch","endpoint":"internal-kyc.bank"}],
  "data_touched":[{"classification":"confidential","egress":false}],
  "policy_decisions":[{"rule":"approval_required","result":"required"}],
  "approval":{"by":"operator@bank","decision":"approved"},
  "prev_hash":"…","hash":"…" }
```

The Action Provenance Record is the tamper-evident chain we already shipped, upgraded to a standard schema and linked to the composition by hash.

### 3.2 Three pieces around an open standard

| Piece | What it is | Role |
|---|---|---|
| **abom-gen** | SDK / agent-runtime hook that auto-emits both artifacts | Open-source → drives adoption of the standard |
| **abom-verify** | Scanner that checks an ABOM against policy — no unapproved models, no PII to egress, every consequential action approved, deployed composition matches the signed manifest | The product risk/compliance teams pay for |
| **The Notary** | Signed, queryable, tamper-evident registry of every ABOM across the org; exports to SIEM and regulators | The neutral system of record — the can't-self-host moat |

---

## 4. Why now

- **The precedent is proven.** SBOM went from nice-to-have to mandated (US EO 14028, EU Cyber Resilience Act). The institutional muscle memory exists.
- **The rail already exists.** CycloneDX shipped **ML-BOM** for models. ABOM is the obvious extension to full agents + runtime provenance. Extend the winner; don't fork the ecosystem.
- **The mandate is coming.** AI Act Art. 12, DORA, NIST AI RMF all converge on agent accountability. We arrive 12–18 months early.
- **Buildable now.** No formal-methods research required (unlike the proof-carrying endgame in §9). Step 0 — the tamper-evident chain — already runs.

---

## 5. Moat & defensibility

1. **Neutrality.** A bill of materials is inherently vendor-neutral — a position only an independent can hold. We sell no model and no agent.
2. **The standard.** Formats are natural monopolies. If "every regulated agent must emit an ABOM" becomes true, there is one reference implementation.
3. **The Notary.** Third-party independence cannot be self-hosted; the neutral, signed registry is the durable, monetizable asset.
4. **Completeness from position.** A trustworthy runtime ABOM requires capturing *every* action — which means sitting in the agent runtime / control plane, where we already are. A bolt-on logger can't match that coverage.

---

## 6. Competitive landscape

| Player | Position | Why they don't own this |
|---|---|---|
| LLM observability (Langfuse, Arize, Helicone) | Dashboards & traces for developers | Built for debugging, not signed, regulator-grade, tamper-evident attestation. Wrong buyer, wrong assurances. |
| SBOM vendors (Anchore, etc.) | Software supply-chain BOMs | Don't model agents (models/tools/prompts/runtime decisions). Could extend in — so move fast on the agent layer. |
| Hyperscaler agent platforms | Managed agent ops | Cloud-locked and not neutral; can't be the sovereign, in-boundary, vendor-neutral attestor regulated buyers need. |
| Model vendors | Sell a model | Cannot credibly be the neutral bill-of-materials layer over *all* models. Natural partners. |
| GRC / audit tooling | Compliance workflows | Operate at the policy/paperwork layer, not at machine-checkable agent provenance. Integration targets. |

**White space:** signed, standard, tamper-evident *runtime* provenance for agentic systems, generated where coverage is complete. No one owns it.

---

## 7. Go-to-market

**Wedge: European regulated financial services.** Risk, compliance, and platform leaders facing AI Act / DORA evidence obligations, who cannot today answer the question below.

**The sentence that sells it:**
> *"Show me, in one signed document, exactly what every AI agent in our bank is made of — and every consequential thing it did — verifiable, and exportable to our SIEM and our regulator."*

**Motion:** land a lighthouse via abom-gen on one high-stakes agent → produce a verified ABOM and catch a real policy violation in abom-verify → become the system of record (Notary) for that team → expand across agents and into adjacent regulated verticals. Open-source adoption of the format seeds the top of funnel beyond the wedge.

---

## 8. Business model

- **Open-source:** the ABOM format and **abom-gen** — adoption is the strategy.
- **Paid:** **abom-verify** (certified policy verification, per agent / per workload) and **the Notary** (registry subscription, priced per deployment + capacity), with on-prem / air-gapped deployment and integration services into regulated estates.
- **Shape:** predictable, on-prem-friendly enterprise pricing; high retention once it is the system of record in compliance workflows.

---

## 9. Roadmap arc

**ABOM (now): accountability.** Record what the agent is and did. Buildable today.
**→ Proof-Carrying Actions (later): prevention.** Escalate from *recording* an action to *gating* it on a machine-checkable proof that it satisfies policy before it runs — a proof is simply a stronger ABOM claim. The accountability record is the on-ramp to the verification endgame.

---

## 10. Risks & mitigations

| Risk | Why it matters | Mitigation |
|---|---|---|
| Standard adoption is a coordination problem | A format no one emits is worthless | Extend CycloneDX (don't fork); win on best generator; anchor a regulated lighthouse who needs it for the deadline |
| "Isn't this just audit logging?" | Looks like observability, commoditises | Lead with the signed standard schema + composition↔runtime linkage + policy verification + neutral notary — not logs |
| Completeness of runtime capture | A partial record isn't trustworthy | Generate from inside the agent runtime / control plane, where we see every action |
| Observability or SBOM vendors extend in | Well-funded adjacents | Regulated-grade signing, tamper-evidence, neutrality and in-boundary posture they aren't built for; move first on the standard |

---

## 11. Immediate next steps

1. Publish **ABOM v0.1** as a public schema that extends CycloneDX ML-BOM.
2. Ship **abom-gen v0** — instrument one agent runtime to emit a signed Composition Manifest + Action Provenance chain (the MVP).
3. Ship **abom-verify v0** — one decidable policy check that catches a real violation (e.g., *unapproved model used* or *confidential data to egress*).
4. Sign a regulated financial-services lighthouse; produce their first verified ABOM.
5. Stand up the Notary as the system of record and convert the lighthouse into a named reference.

---

## 12. Website & messaging starter (abom.ai)

**Hero:** *Know what your agents are made of — and what they did.*
**Subhead:** ABOM is the Agent Bill of Materials: a signed, standard, tamper-evident record of every model, tool, prompt, data source, and decision behind your AI agents. Built for regulated teams under the EU AI Act and DORA.

**Pillars:** **Standard** (extends CycloneDX, open) · **Signed** (tamper-evident, regulator-grade) · **Neutral** (any model, any framework — we sell neither) · **Yours** (runs in your boundary; nothing leaves).

---

*ABOM is the company name and abom.ai the domain. This document is a strategic frame for company formation, not investment or legal advice; regulatory positioning should be validated with qualified counsel.*
