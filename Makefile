.PHONY: install run test lint

install:
	uv sync

run:
	uv run uvicorn app.main:app --reload

test:
	uv run pytest

lint:
	uv run ruff check .
