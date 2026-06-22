# Launch post

*Draft for Show HN / a blog. Tweak the voice to yours before posting.*

---

**Title (Show HN):** Show HN: ABOM – an SBOM for AI agents (`pip install abom-cli`)

**URL:** https://github.com/josephassiga/abom

---

## Post

An AI agent is a black box you can't inventory. Which models does it call? Which
tools and MCP servers can it reach? Which prompts, which vector store, which
guardrails? Today the honest answer is "grep the repo and hope." Software solved
this years ago with the SBOM (and it's now mandated — US EO 14028, the EU Cyber
Resilience Act). Agents have nothing equivalent.

**ABOM is the Agent Bill of Materials.** It's a CLI that scans your repo and emits
a **signed** inventory of everything your agent is made of — and a verifier that
checks it and enforces a policy in CI.

```
$ pip install abom-cli
$ abom scan .

  ABOM · langchain-support-agent
  data sources   1  Chroma
  frameworks     2  LangChain, LangGraph
  models         3  OpenAI (SDK), gpt-4o, gpt-4o-mini
  tools          2  search_orders, issue_refund
  prompts        1  prompts/system.txt
  signed: ed25519 · key 80a12d1f594d5481
  → wrote abom.json

$ abom verify abom.json --policy policy.json
  ✗ 1 finding:
      • [medium] model_allowlist (gpt-4o): declared model not on allowlist
```

It detects models, prompts, tools, MCP servers, frameworks, vector stores and
guardrails from your dependencies and source — each with a `detected_from` so the
manifest is auditable — signs the result with ed25519, and verifies the signature
(plus model-allowlist / residency / egress / approval rules) with a non-zero exit
so it drops straight into CI. There are runnable examples on real LangChain and
CrewAI repos in the repo.

**It's a standard, not just a tool.** The format extends [CycloneDX ML-BOM]
(https://cyclonedx.org/capabilities/mlbom/) — I didn't want to invent a rival BOM
format. The JSON Schema and spec are in [`/spec`](spec/), Apache-2.0, and every
scan output is validated against it in CI.

**Why now:** the EU AI Act's Art. 12 wants record-keeping for high-risk AI, the
OWASP LLM/agent Top 10 keeps flagging supply-chain and excessive-agency risks,
and agents are shipping to prod faster than anyone can account for them.

**Honest limitations (it's v0.1):**
- `abom scan` is a *static* scanner — heuristic detection from deps + source. It
  won't catch a model name built at runtime. Tell me what it misses on your repo.
- Signing uses a local ed25519 key today; Sigstore / keyless signing is next.
- The big roadmap piece is **runtime provenance** — recording what an agent
  actually *did* (not just what it's made of), hash-chained and tamper-evident.
  The format and a reference implementation are already in the repo.

Links: **[github.com/josephassiga/abom](https://github.com/josephassiga/abom)** ·
**[pypi.org/project/abom-cli](https://pypi.org/project/abom-cli/)** ·
**[abom.ai](https://abom.ai)** · spec in [`/spec`](spec/)

I'd love feedback on two things: (1) what components should it detect that it
doesn't, and (2) does the CycloneDX-extension approach feel right, or should the
agent layer be its own format? Apache-2.0, contributions welcome.

---

## Where to post

- **Show HN** — title above; first comment = a short "why I built this" + the demo block.
- **r/LLMOps, r/LocalLLaMA, r/MachineLearning** (as a tool, not an ad).
- **The OWASP GenAI / LLM Top 10 community** and the **CycloneDX** working group — the standard angle lands there.
- **LinkedIn / X** — lead with the one-liner: *"`pip install abom-cli && abom scan .` — the SBOM for AI agents."*

## First-comment seed (HN)

> Author here. The thing I kept hitting: in any real agent codebase, nobody could
> answer "what's actually in this thing" without reading all the code. ABOM makes
> that one signed file. It's deliberately small and static for v0 — the
> interesting hard problem is runtime provenance (what the agent *did*), which is
> the next milestone. Happy to go deep on the detection heuristics or the
> CycloneDX mapping.
