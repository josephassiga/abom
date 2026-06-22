.PHONY: install test up down migrate demo lint

install:
	pip install -e ".[dev]"

test:
	PYTHONPATH=src pytest -q

up:
	docker compose up -d --build

down:
	docker compose down -v

migrate:
	PYTHONPATH=src python scripts/init_db.py
	@echo "(MVP) tables created via metadata. For prod, switch to Alembic migrations."

demo:
	python3 demo/demo.py

lint:
	ruff check src tests
