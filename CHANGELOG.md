# Changelog

All notable changes to ABOM are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and the project aims to
follow [Semantic Versioning](https://semver.org/spec/v2.0.0.html) from 1.0.

## [Unreleased]

### Added
- **ABOM v0.1 specification** (`spec/`) — Composition Manifest and Action
  Provenance Record, extending CycloneDX ML-BOM, with JSON Schema and examples.
- **Reference implementation** (`mvp/src/abom/`): `bom.py` (build composition,
  append provenance, `abom-verify`), `audit.py` (tamper-evident hash chain),
  `cli.py`, `policy.py`.
- **Demo** (`mvp/demo/`) — generate → verify → prove tamper-evidence end to end,
  no infrastructure required.
- Open-source project scaffolding: Apache-2.0 license, contributing guide, code of
  conduct, security policy, governance, CI, and issue/PR templates.

### Notes
- Signing in the reference implementation is an HMAC stand-in (clearly labelled);
  production targets detached ed25519 / Sigstore.
- The control-plane scaffold under `mvp/src/abom/` (API, DB, orchestration) is a
  prototype of the commercial Notary layer and is not part of the v0.1 spec.

[Unreleased]: https://github.com/josephassiga/abom/commits/main
