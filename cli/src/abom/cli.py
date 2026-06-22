"""Thin CLI over the Control API (Typer).

Examples:
  abom project-create --name demo --repo /path/to/repo --test "pytest -q"
  abom run --project <id> --intent "Add input validation to /login"
  abom status <run_id>
  abom audit-verify <run_id>
"""
from __future__ import annotations

import os

import httpx
import typer

app = typer.Typer(help="ABOM control-plane CLI (MVP)")

API = os.environ.get("ABOM_API_URL", "http://localhost:8000")
TOKEN = os.environ.get("ABOM_TOKEN", "dev-token")
H = {"Authorization": f"Bearer {TOKEN}"}


def _client() -> httpx.Client:
    return httpx.Client(base_url=API, headers=H, timeout=30)


@app.command("project-create")
def project_create(name: str, repo: str, test: str = "pytest -q"):
    with _client() as c:
        r = c.post("/v1/projects", json={"name": name, "repo_url": repo, "test_command": test})
        r.raise_for_status()
        typer.echo(r.json()["id"])


@app.command()
def run(project: str, intent: str, max_iterations: int = 4):
    with _client() as c:
        r = c.post("/v1/runs", json={"project_id": project, "intent": intent,
                                     "max_iterations": max_iterations})
        r.raise_for_status()
        typer.echo(r.json()["id"])


@app.command()
def status(run_id: str):
    with _client() as c:
        r = c.get(f"/v1/runs/{run_id}")
        r.raise_for_status()
        data = r.json()
        typer.echo(f"{data['status']:<18} tokens={data['prompt_tokens']}+{data['completion_tokens']}")


@app.command()
def steps(run_id: str):
    with _client() as c:
        r = c.get(f"/v1/runs/{run_id}/steps")
        r.raise_for_status()
        for s in r.json():
            typer.echo(f"{s['seq']:>3}  {s['type']}")


@app.command("audit-verify")
def audit_verify(run_id: str):
    with _client() as c:
        r = c.get("/v1/audit/verify", params={"run_id": run_id})
        r.raise_for_status()
        data = r.json()
        ok = "VALID" if data["valid"] else f"BROKEN at seq {data['broken_seq']} ({data['reason']})"
        typer.echo(f"audit chain: {ok}  ({data['event_count']} events)")


if __name__ == "__main__":
    app()
