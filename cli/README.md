# abom-cli

The reference implementation of [ABOM](../spec/) — the Agent Bill of Materials.
Scan a repo, emit a **signed** Composition Manifest, and **verify** it.

```bash
pip install abom-cli        # (until published: pip install -e .)
abom scan .                 # → abom.json (signed with ed25519)
abom verify abom.json       # check signature
abom verify abom.json --policy policy.json   # + enforce a policy (exit 1 on violations)
```

## Commands

| Command | What it does |
|---|---|
| `abom scan [PATH]` | Detect agent components (models, prompts, tools, MCP servers, frameworks, vector stores, guardrails) and emit a signed Composition Manifest. `-o -` writes to stdout. |
| `abom verify [FILE]` | Verify the ed25519 signature; with `--policy`, enforce model allowlist / residency / egress / approval rules. Non-zero exit on findings (CI-friendly). |
| `abom keygen` | Show (or create) the local ed25519 signing key (`~/.abom/signing_key.pem`, override with `ABOM_KEY`). |
| `abom version` | Print the tool and spec versions. |

### Example

```
$ abom scan .
  ABOM · my-agent @ 1.2.0
  models                  3  gpt-4o-mini, claude-3-5-sonnet, OpenAI (SDK)
  frameworks              2  LangChain, LangGraph
  MCP servers             2  filesystem, github
  tools                   1  lookup_customer
  prompts                 1  prompts/system.txt
  signed: ed25519 · key 5846eabc738b3542
  → wrote abom.json
```

## How detection works

`abom scan` is a static scanner (pure stdlib + `cryptography`):
- **Dependencies** (`requirements*.txt`, `pyproject.toml`, `package.json`) → frameworks, model SDKs, vector stores, guardrails.
- **Source** → concrete model names (`gpt-4o`, `claude-*`, …) and `@tool`-decorated functions.
- **Prompt files** (`*.prompt`, `prompts/*.txt|md`) → hashed.
- **MCP configs** (`mcp.json`, `claude_desktop_config.json`, …) → MCP servers.

Each component records `detected_from` so the manifest is auditable. The output
validates against [`spec/abom-0.1.schema.json`](../spec/abom-0.1.schema.json).

## Signing

`abom scan` signs with **ed25519** (`cryptography`). The key lives at
`~/.abom/signing_key.pem` (override with `ABOM_KEY`); the public key + a short
`key_id` are embedded so `abom verify` is self-contained. A Notary / key registry
pins trusted key ids in production.

## Dev

```bash
make install          # pip install -e ".[dev]"
make test             # pytest (audit chain, scanner, signing)
make scan && make verify
make build            # wheel + sdist + twine check
python demo/demo.py   # generate → verify → tamper-evidence walkthrough
```

## What else is in this package

`src/abom/` also contains a **prototype control-plane** (`api.py`, `db.py`,
`orchestration.py`, the Notary) behind the optional `[server]` extra — the
beginnings of the commercial layer. It is **not** required for `scan`/`verify`
and is not part of the v0.1 spec. See [MVP_SPEC.md](MVP_SPEC.md).
