FROM python:3.12-slim

WORKDIR /app
ENV PYTHONUNBUFFERED=1 PYTHONPATH=/app/src

COPY pyproject.toml ./
RUN pip install --no-cache-dir -e "." || pip install --no-cache-dir \
    fastapi "uvicorn[standard]" pydantic pydantic-settings "sqlalchemy[asyncio]" \
    asyncpg alembic temporalio httpx boto3 "python-jose[cryptography]" typer

COPY src ./src
COPY scripts ./scripts

EXPOSE 8000
CMD ["uvicorn", "abom.api:app", "--host", "0.0.0.0", "--port", "8000"]
