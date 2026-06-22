.PHONY: install test scan verify demo build up down migrate lint

install:
	pip install -e ".[dev]"

test:
	PYTHONPATH=src pytest -q

scan:
	PYTHONPATH=src python -m abom.cli scan . -o abom.json

verify:
	PYTHONPATH=src python -m abom.cli verify abom.json

build:
	rm -rf dist && python -m build && twine check dist/*

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
