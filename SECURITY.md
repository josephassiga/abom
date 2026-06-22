# Security Policy

ABOM is security tooling, so we take vulnerabilities in it seriously.

## Reporting a vulnerability

**Do not open a public issue for security vulnerabilities.**

Report privately to **security@abom.ai**, or use GitHub's
[private vulnerability reporting](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability)
on this repository (Security → Report a vulnerability).

Please include:
- a description of the issue and its impact,
- steps to reproduce or a proof of concept,
- affected version(s) / commit.

We aim to acknowledge reports within **3 business days** and to provide a
remediation timeline after triage. We will credit reporters in the release notes
unless you prefer to remain anonymous.

## Supported versions

ABOM is pre-1.0; security fixes are applied to the `main` branch and the latest
release. Pin a released version for production use.

## Scope

In scope: the ABOM spec, the reference CLI/library (`mvp/src/abom/`), and the
signing / hash-chain / verification logic. The signing in the current reference
implementation uses an HMAC stand-in clearly marked in the code; production
deployments should use detached ed25519 / Sigstore signing.
