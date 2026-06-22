"""abom scan — statically detect an AI agent's components from a repository.

Produces the `agent`, `components`, and `controls` of an ABOM Composition
Manifest by inspecting dependency manifests, source, prompt files, and MCP
configs. Pure stdlib. Best-effort and conservative: it reports what it
can see, with where it saw it (`detected_from`).
"""
from __future__ import annotations

import hashlib
import json
import logging
import re
from pathlib import Path

try:
    import tomllib  # Python 3.11+
except ModuleNotFoundError:  # Python 3.10
    import tomli as tomllib

log = logging.getLogger("abom.scan")

# --- known signals -----------------------------------------------------------
FRAMEWORKS = {
    "langchain": "LangChain", "langchain-core": "LangChain", "langgraph": "LangGraph",
    "crewai": "CrewAI", "llama-index": "LlamaIndex", "llama_index": "LlamaIndex",
    "autogen": "AutoGen", "pyautogen": "AutoGen", "autogen-agentchat": "AutoGen",
    "semantic-kernel": "Semantic Kernel", "haystack-ai": "Haystack",
    "smolagents": "smolagents", "openai-agents": "OpenAI Agents SDK",
    "google-adk": "Google ADK", "google-genai": "Google GenAI", "mcp": "Model Context Protocol",
    "dspy": "DSPy", "dspy-ai": "DSPy", "pydantic-ai": "Pydantic AI",
}
MODEL_SDKS = {
    "openai": "OpenAI", "anthropic": "Anthropic", "mistralai": "Mistral",
    "cohere": "Cohere", "google-generativeai": "Google", "vertexai": "Google Vertex",
    "boto3": "AWS Bedrock", "ollama": "Ollama", "vllm": "vLLM",
    "huggingface-hub": "Hugging Face", "transformers": "Hugging Face",
    "groq": "Groq", "together": "Together", "replicate": "Replicate",
}
VECTOR_STORES = {
    "chromadb": "Chroma", "pinecone-client": "Pinecone", "pinecone": "Pinecone",
    "weaviate-client": "Weaviate", "qdrant-client": "Qdrant", "faiss-cpu": "FAISS",
    "faiss-gpu": "FAISS", "pgvector": "pgvector", "pymilvus": "Milvus", "lancedb": "LanceDB",
}
GUARDRAILS = {
    "guardrails-ai": "Guardrails AI", "nemoguardrails": "NeMo Guardrails",
    "llm-guard": "LLM Guard", "presidio-analyzer": "Presidio", "rebuff": "Rebuff",
}

MODEL_NAME_RE = re.compile(
    r"\b(gpt-4[\w.\-]*|gpt-3\.5[\w.\-]*|o[134][\w.\-]*|chatgpt[\w.\-]*|"
    r"claude-[\w.\-]+|gemini-[\w.\-]+|mistral[\w.\-]*|mixtral[\w.\-]*|"
    r"llama-?[23][\w.\-]*|qwen[\w.\-]*|command-r[\w.\-]*|deepseek[\w.\-]*|phi-?[34][\w.\-]*)\b",
    re.IGNORECASE,
)
TOOL_RE = re.compile(r"@(?:tool|function_tool|tool\([^)]*\))\s*(?:\n\s*)*def\s+(\w+)|"
                     r"@(?:tool|function_tool)\b[\s\S]{0,80}?def\s+(\w+)")
MCP_CONFIG_NAMES = {"mcp.json", ".mcp.json", "claude_desktop_config.json", "mcp_config.json", ".cursor/mcp.json"}
IGNORE_DIRS = {".git", "node_modules", ".venv", "venv", "env", "__pycache__", "dist", "build",
               ".mypy_cache", ".pytest_cache", ".tox", ".ruff_cache", "site-packages", ".next"}
TEXT_EXT = {".py", ".js", ".ts", ".tsx", ".yaml", ".yml", ".json", ".toml", ".env", ".cfg", ".ini", ".md", ".txt"}
MAX_FILE = 1_000_000


def _read(p: Path) -> str:
    try:
        return p.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""


def _sha256(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def _iter_files(root: Path):
    for p in root.rglob("*"):
        if not p.is_file():
            continue
        if any(part in IGNORE_DIRS for part in p.parts):
            continue
        try:
            if p.stat().st_size > MAX_FILE:
                continue
        except OSError:
            continue
        yield p


def _norm_dep(name: str) -> str:
    return re.split(r"[<>=!~ ;\[]", name.strip(), maxsplit=1)[0].strip().lower().replace("_", "-")


def parse_dependencies(root: Path) -> set[str]:
    deps: set[str] = set()
    for req in list(root.glob("requirements*.txt")) + list(root.glob("**/requirements*.txt")):
        if any(part in IGNORE_DIRS for part in req.parts):
            continue
        for line in _read(req).splitlines():
            line = line.strip()
            if line and not line.startswith(("#", "-")):
                deps.add(_norm_dep(line))
    pp = root / "pyproject.toml"
    if pp.exists():
        try:
            data = tomllib.loads(_read(pp))
            for d in data.get("project", {}).get("dependencies", []) or []:
                deps.add(_norm_dep(d))
            poetry = data.get("tool", {}).get("poetry", {}).get("dependencies", {})
            for d in poetry:
                deps.add(_norm_dep(d))
        except Exception:
            pass
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(_read(pkg))
            for section in ("dependencies", "devDependencies"):
                deps.update(_norm_dep(k) for k in data.get(section, {}))
        except Exception:
            pass
    deps.discard("")
    return deps


def _agent_meta(root: Path) -> dict:
    name, version = root.resolve().name, "0.0.0"
    pp = root / "pyproject.toml"
    if pp.exists():
        try:
            data = tomllib.loads(_read(pp))
            proj = data.get("project", {})
            name = proj.get("name", name)
            version = proj.get("version", version)
        except Exception:
            pass
    pkg = root / "package.json"
    if pkg.exists():
        try:
            data = json.loads(_read(pkg))
            name = data.get("name", name)
            version = data.get("version", version)
        except Exception:
            pass
    return {"name": name, "version": version}


def scan(root: Path) -> dict:
    root = Path(root)
    log.info("scanning %s", root.resolve())
    deps = parse_dependencies(root)
    log.info("parsed %d dependencies", len(deps))
    log.debug("dependencies: %s", ", ".join(sorted(deps)) or "(none)")
    components: list[dict] = []
    seen: set[tuple] = set()

    def add(comp: dict):
        key = (comp["type"], comp.get("name"))
        if key not in seen:
            seen.add(key)
            components.append(comp)
            log.debug("+ %-10s %-28s [%s]", comp["type"], comp.get("name", "?"),
                      comp.get("detected_from", "?"),
                      extra={"event": "component", "comp_type": comp["type"],
                             "comp_name": comp.get("name"), "source": comp.get("detected_from")})

    # 1. from dependencies
    for d in sorted(deps):
        if d in FRAMEWORKS:
            add({"type": "framework", "name": FRAMEWORKS[d], "detected_from": f"dependency:{d}"})
        if d in MODEL_SDKS:
            add({"type": "model", "name": f"{MODEL_SDKS[d]} (SDK)", "provider": MODEL_SDKS[d],
                 "egress": d not in ("vllm", "ollama", "transformers"),
                 "detected_from": f"dependency:{d}"})
        if d in VECTOR_STORES:
            add({"type": "dataSource", "kind": "vector-store", "name": VECTOR_STORES[d],
                 "detected_from": f"dependency:{d}"})
        if d in GUARDRAILS:
            add({"type": "policy", "kind": "guardrail", "name": GUARDRAILS[d],
                 "detected_from": f"dependency:{d}"})

    # 2. concrete model names, prompt files, tools, MCP servers — from source
    model_names: set[str] = set()
    for p in _iter_files(root):
        suffix = p.suffix.lower()
        rel = str(p.relative_to(root))
        # prompt files
        if suffix == ".prompt" or "prompt" in p.parent.name.lower() and suffix in (".txt", ".md"):
            text = _read(p)
            add({"type": "prompt", "name": rel, "sha256": _sha256(text),
                 "detected_from": f"file:{rel}"})
        # mcp configs
        if p.name in MCP_CONFIG_NAMES or rel in MCP_CONFIG_NAMES:
            try:
                cfg = json.loads(_read(p))
                for server in (cfg.get("mcpServers") or {}):
                    add({"type": "mcpServer", "name": server, "detected_from": f"file:{rel}"})
            except Exception:
                pass
        if suffix not in TEXT_EXT:
            continue
        text = _read(p)
        for m in MODEL_NAME_RE.findall(text):
            model_names.add(m if isinstance(m, str) else next(filter(None, m)))
        if suffix == ".py" and ("@tool" in text or "@function_tool" in text):
            for groups in TOOL_RE.findall(text):
                fn = next((g for g in groups if g), None)
                if fn:
                    add({"type": "tool", "name": fn, "detected_from": f"file:{rel}"})

    for name in sorted(model_names):
        provider = "external" if not name.lower().startswith(("llama", "qwen", "mistral", "mixtral", "phi", "deepseek")) else "open-weight"
        add({"type": "model", "name": name, "provenance": "referenced in source",
             "egress": provider == "external", "detected_from": "source"})

    log.info("detected %d components", len(components),
             extra={"event": "scan_done", "components": len(components)})
    return {
        "agent": _agent_meta(root),
        "components": components,
        "controls": {"scan": "static", "scanned_path": str(root.resolve().name),
                     "egress": "unknown (static scan)"},
    }
