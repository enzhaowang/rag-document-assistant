# Developer entry points. Run `make help` to list targets.
#
# All Python targets run inside a local virtualenv (.venv) created by `make install`.
# Override the interpreter used to create it with: make install PYTHON_BIN=/path/to/python3.11

PYTHON_BIN ?= python3.11
VENV ?= .venv
PY := $(VENV)/bin/python
UV_COMPILE := uv pip compile pyproject.toml --python-version 3.11 --universal \
	--annotation-style line --custom-compile-command "make lock" --quiet

.DEFAULT_GOAL := help
.PHONY: help install lock lint format test check-llm sample-pdfs ingest api ui eval up down

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-10s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

install: ## Create .venv and install pinned runtime + dev dependencies
	@test -x $(PY) || $(PYTHON_BIN) -m venv $(VENV)
	$(PY) -m pip install --upgrade pip
	$(PY) -m pip install -r requirements-dev.txt

lock: ## Re-resolve pinned requirements from pyproject.toml (requires uv)
	$(UV_COMPILE) -o requirements.txt
	$(UV_COMPILE) --extra dev -o requirements-dev.txt

lint: ## Run ruff lint and format checks
	$(PY) -m ruff check .
	$(PY) -m ruff format --check .

format: ## Auto-format and auto-fix lint issues
	$(PY) -m ruff format .
	$(PY) -m ruff check --fix .

test: ## Run unit tests (integration tests are excluded)
	$(PY) -m pytest -m "not integration"

check-llm: ## Smoke-check the configured LLM/embedding endpoint (real API calls)
	$(PY) -m scripts.check_llm_endpoint

sample-pdfs: ## Regenerate the fictional sample PDFs and FACTS.md in PDF_DIR
	$(PY) scripts/generate_sample_pdfs.py

ingest: ## Parse, chunk and index the PDFs in PDF_DIR
	@echo "ingest: not implemented yet (ingestion pipeline lands in P2/P3)."

api: ## Run the FastAPI backend on port 8080
	@echo "api: not implemented yet (FastAPI backend lands in P5)."

ui: ## Run the Streamlit chat UI
	@echo "ui: not implemented yet (Streamlit UI lands in P6)."

eval: ## Run the evaluation suite and write eval/reports/
	@echo "eval: not implemented yet (evaluation lands in P7)."

up: ## Start the full stack with docker compose
	@echo "up: not implemented yet (docker compose stack lands in P8)."

down: ## Stop the docker compose stack
	@echo "down: not implemented yet (docker compose stack lands in P8)."
