PYTHON ?= python3.13
PORT ?= 8000
FORK_URL ?= http://127.0.0.1:$(PORT)

.PHONY: setup build dev demo test test-browser reset evidence

setup:
	@if command -v uv >/dev/null 2>&1; then \
		if ! test -x .venv/bin/python; then UV_CACHE_DIR=.cache/uv uv venv --python $(PYTHON) .venv; fi; \
		UV_CACHE_DIR=.cache/uv uv pip sync --python .venv/bin/python requirements.lock; \
	else \
		$(PYTHON) -m venv .venv; \
		PIP_DISABLE_PIP_VERSION_CHECK=1 .venv/bin/python -m pip install -r requirements.lock; \
	fi
	npm --prefix frontend ci --no-audit --no-fund --cache "$(CURDIR)/.cache/npm"

build:
	npm --prefix frontend run build

dev:
	.venv/bin/python scripts/dev.py

demo: build
	.venv/bin/python -m uvicorn backend.main:app --host 127.0.0.1 --port $(PORT)

test:
	.venv/bin/python -m pytest -q
	npm --prefix frontend run test:model
	npm --prefix frontend run build

test-browser:
	cd frontend && PLAYWRIGHT_BROWSERS_PATH=../.cache/ms-playwright npx --no-install playwright install chromium
	cd frontend && PLAYWRIGHT_BROWSERS_PATH=../.cache/ms-playwright FORK_URL="$(FORK_URL)" npm run test:e2e

reset:
	.venv/bin/python scripts/reset_demo.py --port $(PORT)

evidence:
	.venv/bin/python scripts/verify_demo.py
