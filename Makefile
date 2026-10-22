# Developer entry points. Run `make help` to list targets.
#
# All Python targets run inside a local virtualenv (.venv) created by `make install`.
# Override the interpreter used to create it with: make install PYTHON_BIN=/path/to/python3.11

PYTHON_BIN ?= python3.11
VENV ?= .venv
API_HOST ?= 127.0.0.1
API_PORT ?= 8080
UI_PORT ?= 8501
PY := $(VENV)/bin/python
UV_COMPILE := uv pip compile pyproject.toml --python-version 3.11 --universal \
	--annotation-style line --custom-compile-command "make lock" --quiet

.DEFAULT_GOAL := help
.PHONY: help install lock lint format test check-llm check-retrieval sample-pdfs ingest api ui eval eval-tune \
	up down logs docker-ingest

help: ## Show available targets
	@awk 'BEGIN {FS = ":.*## "} /^[a-zA-Z_-]+:.*## / {printf "  %-16s %s\n", $$1, $$2}' $(MAKEFILE_LIST)

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

ingest: ## Parse, chunk and index the PDFs in PDF_DIR (pass ARGS=--reset to rebuild)
	$(PY) -m app.ingestion.pipeline $(ARGS)

check-retrieval: ## Measure top-k retrieval hit rate on facts from FACTS.md (real API calls)
	$(PY) scripts/check_retrieval.py

api: ## Run the FastAPI backend (API_HOST/API_PORT, default 127.0.0.1:8080; docs at /docs)
	$(PY) -m uvicorn app.api.main:app --host $(API_HOST) --port $(API_PORT) --no-access-log

ui: ## Run the Streamlit chat UI (UI_PORT, default 8501; talks to the API at API_BASE_URL)
	$(PY) -m streamlit run ui/streamlit_app.py --server.port $(UI_PORT) \
		--server.headless true --browser.gatherUsageStats false --client.toolbarMode viewer

eval: ## Run the evaluation (RAGAS + custom metrics) and write eval/reports/ (real API calls)
	$(PY) -m eval.run_eval $(ARGS)

eval-tune: ## Sweep chunk size / top-k / threshold and write eval/reports/tuning.csv (real API calls)
	$(PY) -m eval.tune $(ARGS)

up: ## Build and start the full stack (chroma + api + ui) with docker compose
	docker compose up -d --build

down: ## Stop the docker compose stack (indexed data is kept in the chroma_data volume)
	docker compose down

logs: ## Follow the logs of the docker compose stack
	docker compose logs -f

docker-ingest: ## Index data/pdfs into the dockerized Chroma (pass ARGS=--reset to rebuild)
	docker compose run --rm api python -m app.ingestion.pipeline $(ARGS)
