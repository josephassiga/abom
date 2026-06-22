# Governance

ABOM is two things with different governance needs: an **open standard** (the ABOM
format) and a **reference implementation** (the `abom` CLI/library). This document
describes how decisions are made today and where we intend to take it.

## Today (pre-1.0)

The project is maintained by the founding maintainers. Decisions are made in the
open via GitHub issues and pull requests. Anyone may propose changes; maintainers
review and merge.

- **Reference implementation** changes follow normal PR review.
- **Spec changes** (anything under `spec/`) require maintainer consensus and a
  clear rationale, because they affect every ABOM ever emitted. Breaking format
  changes bump the spec version (`abom-0.2`, …) and are never silent.

## The standard vs. the company

ABOM follows an **open-core** model:

- **Open (Apache-2.0):** the ABOM format, the JSON Schema, and the reference
  generator/verifier CLI. A bill-of-materials standard only works if it is free
  and ubiquitous, so this layer is, and will remain, open.
- **Commercial:** the hosted, neutral **Notary** (third-party attestation
  registry) and enterprise verification/compliance features. These build on the
  open standard but are not part of it.

Keeping that boundary explicit protects the standard's neutrality: the format is
governed for the community, not for any single vendor.

## Intended direction

To strengthen the standard's neutrality and credibility with regulators, we intend
to propose the **ABOM specification** to a neutral home (e.g. OWASP, OpenSSF, or
the CycloneDX working group it extends) once it stabilizes. The reference
implementation and the commercial Notary remain independently maintained.

## Becoming a maintainer

Sustained, high-quality contributions (code, spec, docs, review, triage) lead to
an invitation to become a maintainer. Maintainers are listed in this file as the
project grows.

## Contact

- General: hello@abom.ai
- Security: security@abom.ai
- Conduct: conduct@abom.ai
