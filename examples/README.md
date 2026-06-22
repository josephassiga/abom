# Examples

Real `abom scan` runs on representative agent repos, with the resulting **signed
ABOMs committed** so you can see exactly what the tool produces.

```bash
pip install abom-cli
```

## [langchain-support-agent/](langchain-support-agent/)

A LangChain customer-support agent (models, retriever, tools, a system prompt).

```
$ abom scan examples/langchain-support-agent
  ABOM · langchain-support-agent
  data sources   1  Chroma
  frameworks     2  LangChain, LangGraph
  models         3  OpenAI (SDK), gpt-4o, gpt-4o-mini
  tools          2  search_orders, issue_refund
  prompts        1  prompts/system.txt
  signed: ed25519 · key 80a12d1f594d5481
```

→ [`langchain-support-agent/abom.json`](langchain-support-agent/abom.json) (9 components, signed)

## [crewai-research-crew/](crewai-research-crew/)

A CrewAI crew (a researcher on `gpt-4o-mini` + a writer on `claude-3-5-sonnet`, a tool).

```
$ abom scan examples/crewai-research-crew
  ABOM · crewai-research-crew
  models      4  Anthropic (SDK), OpenAI (SDK), claude-3-5-sonnet-20241022, gpt-4o-mini
  frameworks  1  CrewAI
  tools       1  kb_lookup
```

→ [`crewai-research-crew/abom.json`](crewai-research-crew/abom.json) (6 components, signed)

## Try it yourself

```bash
abom scan examples/langchain-support-agent            # → abom.json
abom verify examples/langchain-support-agent/abom.json   # ✓ VALID
abom verify examples/langchain-support-agent/abom.json --policy policy.json  # enforce a policy
```

Each component records `detected_from`, and every manifest validates against
[`../spec/abom-0.1.schema.json`](../spec/abom-0.1.schema.json).

## In CI (GitHub Action)

```yaml
- uses: josephassiga/abom/.github/actions/abom-scan@main
  with:
    path: .
    # policy: .abom/policy.json   # optional — fail the build on violations
```

This generates an ABOM for your repo, verifies it, and uploads it as an artifact.
