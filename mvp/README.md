# ABOM — Step-1 MVP (scaffold)

A runnable skeleton of ABOM: generate, sign, and **verify** an Agent Bill of
Materials for an agent run, with a tamper-evident provenance chain. Full spec in
[MVP_SPEC.md](MVP_SPEC.md); system context in the project docs (kept private).

> Status: **scaffold**. The ABOM core (`bom.py`), the tamper-evident hash chain
> (`audit.py`) and their tests/demo are real and pass. The API, Temporal
> workflow, sandbox, and capture hooks are wired but carry `TODO`s where real
> integration (git apply, vLLM, JWKS, runtime taps) belongs.

## What's here

```
src/abom/
  bom.py           ABOM core — Composition Manifest + Action Provenance + abom-verify  ★
  audit.py         tamper-evident hash chain (the provenance substrate)               ★
  config.py        settings
  db.py            async SQLAlchemy models
  schemas.py       API request/response models
  policy.py        simple JSON policy engine (OPA/Rego later)
  models_router.py model client + router (local-only in MVP; MockModelClient for laptops)
  execution.py     sandbox runner + build/test gate (recorded as a provenance fact)
  agents.py        swappable AgentHarness + SimpleAgent
  orchestration.py Temporal workflow + activities + worker
  api.py           FastAPI Control API
  cli.py           Typer CLI
tests/test_audit_chain.py   tamper-evidence unit tests (pure, no deps beyond stdlib)
demo/                        generate → verify → tamper-evidence demo (no infra)
```
★ = real and passing today.

## Quickstart

```bash
# the demo that proves the core — no infrastructure required
make demo            # or: python3 demo/demo.py

# tamper-evidence unit tests (pure)
make test            # or: PYTHONPATH=src python tests/test_audit_chain.py
```

The demo emits a signed Composition Manifest + hash-chained Action Provenance,
runs **abom-verify** on a compliant vs. a violating run (catching a shadow model,
confidential egress, and a missing approval), and shows that scrubbing the
evidence breaks the chain. `ABOM_MODEL_USE_MOCK=true` (default) means it runs with
no GPU.

Full local stack (Postgres, Temporal, MinIO, API, worker):
```bash
cp .env.example .env && make up && make migrate
```
All settings use the `ABOM_` env prefix (see [.env.example](.env.example)).

## The ABOM core

- **Composition Manifest** — `bom.build_composition(...)` returns a signed manifest
  (extends CycloneDX ML-BOM) with a `composition_sha256` join key.
- **Action Provenance** — `bom.append_action(...)` appends a hash-chained record
  (reusing the audit chain) for each consequential action.
- **abom-verify** — `bom.verify_abom(composition, chain, policy)` returns findings
  for: signature, chain integrity, composition-match, model allowlist + drift,
  data residency, egress allowlist, and approval coverage.

*(The MVP signature is an HMAC stand-in, clearly labelled; production uses
detached ed25519 / cosign — see ARCHITECTURE.md §3.6.)*

## Notable TODOs before this is real

- **Capture completeness** — wire `abom-gen` into the agent runtime / model router
  / tool gateway (+ an eBPF egress backstop) so no action is missed. This is the
  product's hardest and most important property.
- Real detached **ed25519 / cosign** signing with keys in Vault/KMS.
- The **Notary** — persist manifests/provenance/attestations to an append-only,
  queryable registry with SIEM + CycloneDX export.
- `execution.Sandbox.apply_patch` → real `git apply`; `api.current_principal` →
  real JWKS validation; Alembic migrations; gVisor/Kata sandbox.
