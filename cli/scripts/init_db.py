"""Create all tables (MVP convenience before Alembic migrations exist).

Usage:  PYTHONPATH=src python scripts/init_db.py
For real deployments, generate Alembic migrations from the models instead.
"""
import asyncio

from abom.db import Base, engine


async def main() -> None:
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("abom: tables created")


if __name__ == "__main__":
    asyncio.run(main())
