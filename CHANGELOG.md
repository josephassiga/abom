# Changelog

All notable changes to ABOM are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) from 1.0.

## [Unreleased]

### Added
- **`abom` CLI** (`abom-cli` on PyPI):
  - `abom scan` — static scanner that detects an agent's components (models,
    prompts, tools, MCP servers, frameworks, vector stores, guardrails) from
    dependencies and source, and emits a **signed Composition Manifest**.
  - `abom verify` — verifies the ed25519 signature and, with `--policy`, enforces
    model allowlist / residency / egress / approval rules (non-zero exit on findings).
  - `abom keygen`, `abom version`.
- **Real ed25519 signing** (`sign.py`) — replaces the earlier HMAC stand-in; keys
  in `~/.abom/`, public key + key id embedded for self-contained verification.
- **ABOM v0.1 specification** (`spec/`) — Composition Manifest and Action
  Provenance Record, extending CycloneDX ML-BOM, with JSON Schema and examples.
  `abom scan` output validates against the schema (enforced in CI).
- **GitHub Action** (`.github/actions/abom-scan`) — run `abom scan`/`verify` in CI.
- **PyPI release pipeline** (`.github/workflows/release.yml`, `PUBLISHING.md`) —
  Trusted Publishing on tag.
- **Demo** (`cli/demo/`) — generate → verify → prove tamper-evidence, no infra.
- Open-source scaffolding: Apache-2.0 license, contributing/governance/security,
  CI, issue/PR templates.

### Notes
- The CLI core is dependency-light (`typer`, `cryptography`). The prototype
  control-plane (`api.py`, `db.py`, `orchestration.py`) lives behind the optional
  `[server]` extra and is not part of the v0.1 spec.

[Unreleased]: https://github.com/josephassiga/abom/commits/main
