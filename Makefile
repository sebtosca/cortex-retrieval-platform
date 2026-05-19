.PHONY: help up down install lint test test-unit test-integration eval benchmark slice worker ingest-docs ingest-prices

help:
	@echo "Cortex — Production RAG Platform"
	@echo ""
	@echo "  make up            Start all services (docker-compose)"
	@echo "  make down          Stop all services"
	@echo "  make install       Install Python dependencies"
	@echo "  make lint          Run ruff + mypy"
	@echo "  make test          Run full test suite"
	@echo "  make test-unit     Run unit tests only"
	@echo "  make test-int      Run integration tests (requires running services)"
	@echo "  make eval          Run RAGAS evaluation suite"
	@echo "  make benchmark     Run retrieval benchmark (dense/sparse/hybrid/rerank)"
	@echo "  make slice         Run vertical slice smoke test"
	@echo "  make ingest-docs   Ingest all company PDFs into production Qdrant collection"
	@echo "  make worker        Start ARQ ingestion worker (requires Redis)"
	@echo "  make ingest-prices Seed PostgreSQL with 90 days of OHLCV for tracked tickers"

up:
	docker compose up -d

down:
	docker compose down

install:
	pip install -e ".[dev,benchmarks]"

lint:
	ruff check . && mypy .

test:
	pytest tests/ -v --cov=. --cov-report=term-missing

test-unit:
	pytest tests/unit/ -v

test-int:
	pytest tests/integration/ -v

eval:
	pytest tests/evaluation/ -v -s

benchmark:
	python benchmarks/retrieval_benchmark.py

slice:
	python scripts/vertical_slice.py

ingest-docs:
	python scripts/ingest_documents.py

worker:
	arq api.worker.WorkerSettings

ingest-prices:
	python scripts/ingest_prices.py
