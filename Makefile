.PHONY: install run test lint compare

install:
	uv sync

run:
	@[ -n "$(APP)" ] || { echo "Sett APP, f.eks.: make run APP=<modul>:<variabel>"; exit 1; }
	uv run uvicorn $(APP) --reload

test:
	@uv run pytest; status=$$?; [ $$status -eq 0 ] || [ $$status -eq 5 ]

lint:
	uv run ruff check .

compare:
	@[ "$$(git branch --show-current)" = main ] || { echo "Bytt til main først: git switch main"; exit 1; }
	git pull --ff-only
	python3 metrics/compare.py $(if $(SPLIT),--split $(SPLIT))
	@command -v open >/dev/null && open metrics/comparison.html || echo "Åpne metrics/comparison.html"
