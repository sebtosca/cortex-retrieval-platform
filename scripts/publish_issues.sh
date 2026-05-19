#!/usr/bin/env bash
# Run after: gh auth login
# Creates all 11 Cortex issues in dependency order.
set -e

REPO="sebtosca/Cortex-Production-Grade-Retrieval-and-Intelligence-Platform"

echo "Publishing Cortex issues to $REPO..."

I1=$(gh issue create --repo "$REPO" \
  --title "Vertical stack proof: PDF → bge-m3 → Qdrant → Claude SSE stream" \
  --body "$(cat <<'EOF'
## What to build
Prove the full tech stack works end-to-end before any abstraction. `scripts/vertical_slice.py`: one PDF → bge-m3 embed → store in Qdrant → hybrid query → cross-encoder rerank → Claude Haiku SSE stream via LiteLLM.

## Acceptance criteria
- [ ] bge-m3 produces both dense and sparse vectors from a single model pass
- [ ] Qdrant stores and retrieves documents using hybrid (dense+sparse) search
- [ ] Cross-encoder reranker re-scores top-20 candidates and returns top-5
- [ ] Claude Haiku streams a response via SSE using LiteLLM
- [ ] Full pipeline runs end-to-end in under 3 seconds on a single document

## Blocked by
None — can start immediately
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I1: Vertical stack proof"

I2=$(gh issue create --repo "$REPO" \
  --title "Modular package structure: ingestion, embeddings, retrieval, llm modules" \
  --body "$(cat <<'EOF'
## What to build
Refactor the vertical slice into clean, independently testable Python modules: `ingestion/` (PDF loading, chunking, metadata), `embeddings/` (bge-m3 wrapper, caching), `retrieval/` (Qdrant client, hybrid search, reranker), `llm/` (LiteLLM wrapper, prompt templates, streaming).

## Acceptance criteria
- [ ] Each module has a clear public interface (no circular imports)
- [ ] `make slice` still runs green using the refactored modules
- [ ] Unit tests exist for chunking logic, prompt formatting, and score normalization
- [ ] `ruff check .` passes

## Blocked by
- #$I1
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I2: Modular package structure"

I3=$(gh issue create --repo "$REPO" \
  --title "FastAPI async API: /query SSE stream, /ingest, /health" \
  --body "$(cat <<'EOF'
## What to build
Build the production API surface. Endpoints: `POST /query` streams SSE tokens from Claude Haiku, `POST /ingest` accepts PDF upload and returns job ID, `GET /health` liveness check, `GET /traces` link to Jaeger UI.

## Acceptance criteria
- [ ] `POST /query` streams tokens via SSE as they arrive from the LLM
- [ ] `POST /ingest` returns `{"job_id": "..."}` immediately (non-blocking)
- [ ] `GET /health` returns 200 with service status
- [ ] Integration test hits real Qdrant running in Docker
- [ ] `httpx` async test client verifies SSE stream delivers tokens

## Blocked by
- #$I2
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I3: FastAPI async API"

I4=$(gh issue create --repo "$REPO" \
  --title "Async ingestion queue: ARQ + Redis, job ID + status endpoint" \
  --body "$(cat <<'EOF'
## What to build
Make PDF ingestion non-blocking using ARQ (async Redis queue). `GET /ingest/{job_id}/status` returns job state: `queued | processing | complete | failed`.

## Acceptance criteria
- [ ] `POST /ingest` enqueues job and returns job ID within 100ms
- [ ] ARQ worker processes: PDF parse → chunk → embed → store in Qdrant
- [ ] `GET /ingest/{job_id}/status` reflects real job state
- [ ] Failed jobs surface an error message in the status response
- [ ] Integration test verifies full queue-to-completion flow

## Blocked by
- #$I3
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I4: Async ingestion queue"

I5=$(gh issue create --repo "$REPO" \
  --title "PostgreSQL financial data layer + scheduled yfinance ingestion + Redis cache" \
  --body "$(cat <<'EOF'
## What to build
Store financial metrics in PostgreSQL and serve them via Redis cache. Scheduled job fetches yfinance data for [GOOGL, MSFT, IBM, NVDA, AMZN] and upserts into `company_metrics` table. Redis caches hot lookups with a 1-hour TTL.

## Acceptance criteria
- [ ] `company_metrics` table schema covers: market cap, P/E, dividend yield, beta, total revenue
- [ ] Scheduled ingestion job runs and upserts without duplicates
- [ ] API serves financial metrics from Redis (cache hit) or PostgreSQL (cache miss)
- [ ] Cache miss falls through to DB and populates Redis
- [ ] Unit test verifies upsert idempotency

## Blocked by
- #$I2
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I5: PostgreSQL financial data layer"

I6=$(gh issue create --repo "$REPO" \
  --title "OTel tracing → Jaeger: retrieval, rerank, generation as distinct spans" \
  --body "$(cat <<'EOF'
## What to build
Instrument the full RAG pipeline with OpenTelemetry distributed tracing. Distinct spans: `retrieval` (Qdrant query latency), `rerank` (cross-encoder latency), `generation` (Claude time-to-first-token + total).

## Acceptance criteria
- [ ] Every `POST /query` request produces a trace in Jaeger UI
- [ ] Retrieval, rerank, and generation are separate child spans with timing
- [ ] Token count and model name are recorded as span attributes
- [ ] `docker-compose up` starts Jaeger and traces are visible at `localhost:16686`
- [ ] OTel adds < 5ms overhead to p50 request latency

## Blocked by
- #$I3
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I6: OTel tracing"

I7=$(gh issue create --repo "$REPO" \
  --title "RAGAS evaluation harness + custom financial hallucination metric" \
  --body "$(cat <<'EOF'
## What to build
Build the evaluation dataset and scoring pipeline. RAGAS TestsetGenerator produces 50+ synthetic question/answer pairs from company PDFs. 10 questions manually verified against source documents (gold set). Standard metrics: faithfulness, answer_relevancy, context_precision, context_recall. Custom metric: financial hallucination — does the answer fabricate a project name or initiative not in the retrieved context? (Claude Sonnet judge, scored 1–5).

## Acceptance criteria
- [ ] `make eval` runs the full evaluation suite and prints a metrics table
- [ ] Gold set of 10 questions committed to `tests/evaluation/gold_questions.json`
- [ ] Custom hallucination metric scores each answer 1–5 with justification
- [ ] Results saved to `evaluation/results/latest.json` for CI comparison
- [ ] All metrics documented in `docs/EVALUATION.md`

## Blocked by
- #$I2
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I7: RAGAS evaluation harness"

I8=$(gh issue create --repo "$REPO" \
  --title "CI quality gate: RAGAS score threshold fails the build" \
  --body "$(cat <<'EOF'
## What to build
Fail the CI build if RAGAS scores regress below thresholds. Starting thresholds (tunable): faithfulness >= 0.80, context_recall >= 0.75, hallucination_rate <= 0.15. Thresholds configurable in `configs/eval_thresholds.yaml`.

## Acceptance criteria
- [ ] GitHub Actions `eval-gate` job runs on every push to `main`
- [ ] Build fails with a clear message if any threshold is breached
- [ ] Thresholds are configurable in `configs/eval_thresholds.yaml` (not hardcoded)
- [ ] Baseline scores from issue #$I7 committed so the gate has a reference point

## Blocked by
- #$I7
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I8: CI quality gate"

I9=$(gh issue create --repo "$REPO" \
  --title "Retrieval benchmark suite: dense → sparse → hybrid → hybrid+rerank" \
  --body "$(cat <<'EOF'
## What to build
Produce the benchmark table that becomes the centrepiece of the README and interview story. Compare four retrieval strategies on the gold question set. Also measure reranker latency at k=3, k=5, k=10, k=20 to find the quality/latency knee — this is the core engineering story.

| Strategy | RAGAS Faithfulness | Context Recall | p50 Latency |
|---|---|---|---|
| Dense only | | | |
| Sparse (bge-m3) only | | | |
| Hybrid (dense+sparse) | | | |
| Hybrid + reranker (k=5) | | | |

## Acceptance criteria
- [ ] `make benchmark` produces the full table and saves to `benchmarks/results/retrieval.json`
- [ ] Latency measured at p50 and p95 for each strategy
- [ ] Reranker k-sweep (k=3/5/10/20) shows the quality/latency tradeoff curve
- [ ] Results committed to repo so the table is reproducible

## Blocked by
- #$I7
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I9: Retrieval benchmark suite"

I10=$(gh issue create --repo "$REPO" \
  --title "docker-compose full stack + make up smoke test" \
  --body "$(cat <<'EOF'
## What to build
Wire all services into a single `docker-compose up` that starts a fully working system. Services: Qdrant, PostgreSQL, Redis, Jaeger, API server, ARQ worker.

## Acceptance criteria
- [ ] `make up` starts all services with no manual steps
- [ ] `make slice` passes against the running stack
- [ ] Health checks defined for each service
- [ ] `make down` cleans up cleanly
- [ ] README quickstart works from a cold clone

## Blocked by
- #$I3
- #$I4
- #$I5
- #$I6
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I10: docker-compose full stack"

I11=$(gh issue create --repo "$REPO" \
  --title "README: architecture diagrams, benchmark table, engineering story" \
  --body "$(cat <<'EOF'
## What to build
Write the portfolio-facing documentation that makes the engineering depth legible to a recruiter or technical interviewer.

## Acceptance criteria
- [ ] Architecture diagram covers ingestion flow, query flow, observability flow
- [ ] Benchmark table from issue #$I9 embedded with commentary
- [ ] Engineering story section explains the reranker k-sweep finding and hallucination characterization
- [ ] Quickstart: `git clone → cp .env.example .env → make up → make slice` works from cold clone
- [ ] Tradeoffs section discusses: chunking strategy, hybrid vs dense, reranker depth, caching decisions

## Blocked by
- #$I9
- #$I10
EOF
)" | grep -o '[0-9]*$')
echo "Created #$I11: README + engineering story"

echo ""
echo "All 11 issues created. View at: https://github.com/$REPO/issues"
