"""Tests for `abom scan` — detection, signing, and spec conformance."""
import json
from pathlib import Path

from abom import bom, scan as scanner

FIX = Path(__file__).parent / "fixtures" / "sample-agent"
SCHEMA = Path(__file__).parents[2] / "spec" / "abom-0.1.schema.json"


def test_scan_detects_components():
    result = scanner.scan(FIX)
    by_type = {}
    for c in result["components"]:
        by_type.setdefault(c["type"], set()).add(c.get("name"))

    assert "LangChain" in by_type.get("framework", set())
    assert "LangGraph" in by_type.get("framework", set())
    assert by_type.get("model"), "should detect models"
    names = {n for ns in by_type.values() for n in ns}
    assert any("gpt-4o" in (n or "").lower() for n in names)
    assert any("claude-3-5-sonnet" in (n or "").lower() for n in names)
    assert "filesystem" in by_type.get("mcpServer", set())
    assert "github" in by_type.get("mcpServer", set())
    assert "lookup_customer" in by_type.get("tool", set())
    assert by_type.get("dataSource"), "chromadb -> data source (vector store)"
    assert by_type.get("policy"), "guardrails-ai -> policy/guardrail"
    assert any("prompts/system.txt" in (n or "") for n in by_type.get("prompt", set()))


def test_scan_emits_signed_manifest():
    result = scanner.scan(FIX)
    manifest = bom.build_composition(result["agent"], result["components"], result["controls"])
    assert manifest["type"] == "CompositionManifest"
    assert manifest["signature"]["alg"] == "ed25519"
    assert bom.verify_signature(manifest) is True


def test_tampered_manifest_fails_signature():
    result = scanner.scan(FIX)
    manifest = bom.build_composition(result["agent"], result["components"], result["controls"])
    manifest["agent"]["name"] = "evil-rename"  # tamper after signing
    assert bom.verify_signature(manifest) is False


def test_scanned_manifest_validates_against_spec():
    import jsonschema
    schema = json.loads(SCHEMA.read_text())
    result = scanner.scan(FIX)
    manifest = bom.build_composition(result["agent"], result["components"], result["controls"])
    jsonschema.validate(manifest, schema)


def test_verify_abom_clean_for_unconstrained_policy():
    result = scanner.scan(FIX)
    manifest = bom.build_composition(result["agent"], result["components"], result["controls"])
    out = bom.verify_abom(manifest)  # no policy -> structural only
    assert out["ok"] is True
    assert out["components"] >= 5


def test_verify_abom_flags_unapproved_model():
    result = scanner.scan(FIX)
    manifest = bom.build_composition(result["agent"], result["components"], result["controls"])
    out = bom.verify_abom(manifest, policy={"allowed_models": ["local/only-this-one"]})
    assert out["ok"] is False
    assert any(f["rule"] == "model_allowlist" for f in out["findings"])
