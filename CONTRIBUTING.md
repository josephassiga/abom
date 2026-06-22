# Contributing to ABOM

Thanks for your interest in ABOM — the open standard and tooling for an **Agent
Bill of Materials**. Contributions to the spec, the reference implementation, the
docs, and the examples are all welcome.

## Ways to contribute

- **The spec** ([`spec/`](spec/)) — propose fields, examples, or clarifications to
  the ABOM format. Spec changes are the highest-impact contributions; see
  [GOVERNANCE.md](GOVERNANCE.md) for how the format evolves.
- **The reference implementation** ([`mvp/`](mvp/)) — the `abom` CLI and library
  (`bom.py`, `audit.py`, `cli.py`, `policy.py`).
- **Docs & examples** — getting-started guides, integrations, sample ABOMs.

## Dev setup

```bash
cd mvp
pip install -e ".[dev]"      # FastAPI, Temporal, SQLAlchemy, pytest, ruff, …

# fast checks — no infrastructure needed
PYTHONPATH=src pytest tests/ -q     # tamper-evidence unit tests
python demo/demo.py                 # generate → verify → tamper-evidence demo
ruff check src                      # lint
```

The tamper-evident core (`audit.py`, `bom.py`) and the demo are **pure stdlib**, so
they run on a laptop with no GPU, database, or network.

## Pull requests

1. Fork, branch from `main` (`feature/…` or `fix/…`).
2. Keep changes focused; add or update tests for behaviour changes.
3. Run the checks above — CI runs the same on every PR.
4. Open a PR using the template; link any related issue.

## Sign your commits (DCO)

We use the [Developer Certificate of Origin](https://developercertificate.org/).
Add a sign-off to each commit:

```bash
git commit -s -m "your message"
```

This certifies you wrote the patch or have the right to submit it under the
project's Apache-2.0 license.

## Schema changes

If you change the ABOM format, update **all** of:
- `spec/abom-<version>.schema.json`
- `spec/README.md` (the human-readable spec)
- `spec/examples/` (keep the examples valid against the schema)
- the reference implementation in `mvp/src/abom/bom.py`

## Code of conduct

Participation is governed by our [Code of Conduct](CODE_OF_CONDUCT.md).
