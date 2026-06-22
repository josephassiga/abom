"""abom — the Agent Bill of Materials CLI.

    abom scan .                 # detect components, emit a signed ABOM
    abom verify abom.json       # check signature (and policy, if given)
    abom keygen                 # show the local ed25519 signing key
    abom version

Exit code is non-zero when verification finds violations, so it drops into CI.
"""
from __future__ import annotations

import json
from pathlib import Path

import typer

from . import __version__, bom, log, scan as scanner, sign

app = typer.Typer(
    add_completion=False,
    no_args_is_help=True,
    help="ABOM — know what your AI agents are made of, and prove it.",
)

TYPE_LABEL = {
    "model": "models", "tool": "tools", "prompt": "prompts", "dataSource": "data sources",
    "policy": "policies / guardrails", "framework": "frameworks", "mcpServer": "MCP servers",
}


@app.command()
def scan(
    path: str = typer.Argument(".", help="Repository or directory to scan."),
    output: str = typer.Option("abom.json", "-o", "--output", help="Output file ('-' for stdout)."),
    sign_manifest: bool = typer.Option(True, "--sign/--no-sign", help="ed25519-sign the manifest."),
    name: str = typer.Option(None, "--name", help="Override the detected agent name."),
    version: str = typer.Option(None, "--agent-version", help="Override the detected agent version."),
    verbose: int = typer.Option(0, "-v", "--verbose", count=True, help="-v info, -vv debug (to stderr)."),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Errors only."),
):
    """Scan a repo and emit a signed ABOM Composition Manifest."""
    log.setup(verbose, quiet)
    root = Path(path)
    if not root.exists():
        typer.secho(f"path not found: {path}", fg="red", err=True)
        raise typer.Exit(2)

    result = scanner.scan(root)
    if name:
        result["agent"]["name"] = name
    if version:
        result["agent"]["version"] = version
    manifest = bom.build_composition(
        result["agent"], result["components"], result["controls"], sign=sign_manifest
    )

    text = json.dumps(manifest, indent=2)
    if output == "-":
        typer.echo(text)
    else:
        Path(output).write_text(text)

    a = manifest["agent"]
    typer.secho(f"\n  ABOM · {a['name']} @ {a['version']}", fg="cyan", bold=True)
    by_type: dict[str, list] = {}
    for c in manifest["components"]:
        by_type.setdefault(c["type"], []).append(c.get("name", "?"))
    if not by_type:
        typer.secho("  no agent components detected (is this an agent repo?)", fg="yellow")
    for t, names in by_type.items():
        typer.echo(f"  {TYPE_LABEL.get(t, t):22} {len(names):>2}  " + ", ".join(names[:6])
                   + (" …" if len(names) > 6 else ""))
    sig = manifest.get("signature", {})
    if sig:
        typer.secho(f"  signed: {sig.get('alg')} · key {sig.get('key_id', '?')}", fg="green")
    typer.echo(f"  composition_sha256: {manifest['composition_sha256'][:16]}…")
    if output != "-":
        typer.secho(f"  → wrote {output}\n", fg="cyan")


@app.command()
def verify(
    abom_file: str = typer.Argument("abom.json", help="ABOM file to verify."),
    policy_file: str = typer.Option(None, "--policy", "-p", help="Policy JSON to enforce."),
    verbose: int = typer.Option(0, "-v", "--verbose", count=True, help="-v info, -vv debug (to stderr)."),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Errors only."),
):
    """Verify an ABOM's signature, and (with --policy) its compliance."""
    log.setup(verbose, quiet)
    try:
        doc = json.loads(Path(abom_file).read_text())
    except Exception as exc:
        typer.secho(f"could not read {abom_file}: {exc}", fg="red", err=True)
        raise typer.Exit(2)
    if doc.get("type") != "CompositionManifest":
        typer.secho("not a Composition Manifest (verify expects `abom scan` output)", fg="red", err=True)
        raise typer.Exit(2)

    policy = json.loads(Path(policy_file).read_text()) if policy_file else None
    result = bom.verify_abom(doc, [], policy)

    if result["ok"]:
        typer.secho(f"\n  ✓ VALID — signature OK, {result['components']} components"
                    + (", policy clean" if policy else "") + "\n", fg="green", bold=True)
        raise typer.Exit(0)

    typer.secho(f"\n  ✗ {len(result['findings'])} finding(s):", fg="red", bold=True)
    for f in result["findings"]:
        loc = f.get("component") or (f"seq {f['seq']}" if "seq" in f else "-")
        typer.echo(f"      • [{f['severity']}] {f['rule']} ({loc}): {f['detail']}")
    typer.echo("")
    raise typer.Exit(1)


@app.command()
def keygen(
    show_private: bool = typer.Option(False, "--show-private", help="Print the private key path."),
    verbose: int = typer.Option(0, "-v", "--verbose", count=True, help="-v info, -vv debug (to stderr)."),
    quiet: bool = typer.Option(False, "-q", "--quiet", help="Errors only."),
):
    """Show (or create) the local ed25519 signing key."""
    log.setup(verbose, quiet)
    key = sign.load_or_create_key()
    pub_b64 = sign._pub_b64(key.public_key())
    path = sign.default_key_path()
    typer.secho("  ABOM signing key", fg="cyan", bold=True)
    typer.echo(f"  key_id:     {sign.key_id(pub_b64)}")
    typer.echo(f"  public_key: {pub_b64}")
    if show_private:
        typer.echo(f"  private:    {path}")
    typer.secho(f"  stored at {path} (override with ABOM_KEY)", fg="bright_black")


@app.command()
def version():
    """Print the abom and ABOM-spec versions."""
    typer.echo(f"abom {__version__} · ABOM spec v{bom.ABOM_VERSION}")


if __name__ == "__main__":
    app()
