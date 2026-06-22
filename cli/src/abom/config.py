"""Runtime configuration, loaded from environment / .env (see .env.example)."""
from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="ABOM_", env_file=".env", extra="ignore")

    # storage / infra
    database_url: str = "postgresql+asyncpg://abom:abom@localhost:5432/abom"
    temporal_host: str = "localhost:7233"
    temporal_namespace: str = "default"
    task_queue: str = "abom-cli"

    s3_endpoint: str = "http://localhost:9000"
    s3_access_key: str = "minioadmin"
    s3_secret_key: str = "minioadmin"
    s3_bucket: str = "abom-artifacts"

    # model serving (local, OpenAI-compatible — e.g. vLLM)
    model_base_url: str = "http://localhost:8001/v1"
    model_name: str = "local/qwen2.5-coder"
    model_use_mock: bool = True  # MVP default: run without a GPU

    # auth
    oidc_jwks_url: str = ""               # empty -> dev mode
    oidc_audience: str = "abom"
    dev_static_token: str = "dev-token"   # dev only

    # execution
    sandbox_image: str = "python:3.12-slim"
    workspace_root: str = "/tmp/abom-workspaces"
    gate_timeout_seconds: int = 600


settings = Settings()
