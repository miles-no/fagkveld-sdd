.PHONY: install run test lint

install:
	uv sync

run:
	@[ -n "$(APP)" ] || { echo "Sett APP, f.eks.: make run APP=<modul>:<variabel>"; exit 1; }
	uv run uvicorn $(APP) --reload

test:
	@uv run pytest; status=$$?; [ $$status -eq 0 ] || [ $$status -eq 5 ]

lint:
	uv run ruff check .
