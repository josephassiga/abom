# ABOM demo — generate · verify · prove tamper-evidence

This is the demonstration that matters for ABOM: it generates an **Agent Bill of
Materials** for an agent run and shows **abom-verify** catching real policy
violations a raw log would let ship silently — then proves the record can't be
quietly scrubbed.

## Run it

```bash
cd cli
python3 demo/demo.py        # or: make demo
```

No infrastructure required — no Temporal, Postgres, GPU. The model is a
deterministic mock; the **test gate is a real subprocess**, and the **signing,
hash-chaining, and policy verification are real** ([../src/abom/bom.py](../src/abom/bom.py),
[../src/abom/audit.py](../src/abom/audit.py)).

## What it does

It emits one signed **Composition Manifest** (what the agent is made of) and runs
an agent two ways, each producing a hash-chained **Action Provenance** chain
(what the agent did), then runs **abom-verify**:

| Run | What happens | abom-verify |
|---|---|---|
| **Compliant** | approved model, no bad egress, consequential action approved | **CLEAN** — 0 findings |
| **Violating** | shadow (unapproved) model, confidential data egressed to an unapproved endpoint, consequential action with no approval | **BLOCKED** — 5 findings |

The five findings on the violating run: `model_allowlist`, `composition_drift`,
`approval_coverage`, `residency`, `egress_allowlist`.

Then it tampers — edits the provenance record to **erase the egress** — and shows
the hash chain breaks (`chain_integrity` finding), so the evidence can't be
silently scrubbed.

## Expected output

```
abom-verify [compliant]: CLEAN ✓  over 2 actions
abom-verify [violating]: BLOCKED ✗  (5 findings)  over 2 actions
    • [high] model_allowlist (seq 0): unapproved model used: external/gpt-4o
    • [high] composition_drift (seq 0): runtime model not in signed manifest: external/gpt-4o
    • [high] approval_coverage (seq 0): consequential action without approval
    • [high] residency (seq 1): confidential data egressed
    • [medium] egress_allowlist (seq 1): egress to unapproved endpoint: telemetry.vendor.example
scrubbing the record → chain integrity: BROKEN (detected)
✓ DEMO ASSERTIONS PASSED
```

## Artifacts (written to `demo/out/`)

- `composition.json` — the signed Composition Manifest.
- `provenance_compliant.json` / `provenance_violating.json` — the hash-chained Action Provenance chains.
- `verify.json` — the machine-checkable abom-verify results.

## What this proves — and what it doesn't

It proves the four ABOM mechanics: **composition** is captured and signed,
**provenance** is recorded and tamper-evident, **verify** catches policy
violations that would otherwise ship silently, and scrubbing the evidence is
**detected**.

It does **not** prove capture *completeness* — here the actions are supplied by
the demo. The real product earns completeness by generating from inside the agent
runtime / control plane (see the project docs (kept private) §3.2),
which is the next thing to build and the metric to put in front of a design
partner.
