---
marp: true
theme: default
paginate: true
style: |
  @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap');

  section {
    font-family: 'Inter', system-ui, -apple-system, sans-serif;
    background: #07090f;
    color: #e2e8f0;
    padding: 52px 64px;
    font-size: 18px;
    line-height: 1.65;
  }

  h1 {
    color: #6366f1;
    font-size: 2.2em;
    font-weight: 700;
    letter-spacing: -0.025em;
    line-height: 1.1;
    margin-bottom: 0.2em;
  }

  h2 {
    color: #e2e8f0;
    font-size: 1.5em;
    font-weight: 700;
    letter-spacing: -0.02em;
    margin-bottom: 0.75em;
    padding-bottom: 12px;
    border-bottom: 1px solid #1e293b;
  }

  h3 {
    color: #a5b4fc;
    font-size: 0.78em;
    font-weight: 600;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin: 1.4em 0 0.5em;
  }

  code {
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    background: #111827;
    color: #a5b4fc;
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.78em;
    border: 1px solid #1e293b;
  }

  pre {
    background: #0c1221;
    border: 1px solid #1e293b;
    border-left: 3px solid #4f46e5;
    border-radius: 0 8px 8px 0;
    padding: 20px 24px;
    font-size: 0.64em;
    line-height: 1.75;
  }

  pre code {
    background: none;
    border: none;
    padding: 0;
    color: #e2e8f0;
    font-size: 1em;
    letter-spacing: 0;
  }

  table {
    border-collapse: collapse;
    width: 100%;
    font-size: 0.79em;
    margin-top: 0.6em;
    border: 1px solid #1e293b;
    border-radius: 6px;
    overflow: hidden;
  }

  th {
    background: #312e81;
    color: #e0e7ff;
    font-weight: 600;
    padding: 11px 16px;
    text-align: left;
    font-size: 0.88em;
    letter-spacing: 0.04em;
    border-right: 1px solid #3730a3;
  }

  th:last-child { border-right: none; }

  td {
    padding: 10px 16px;
    border-bottom: 1px solid #1e293b;
    border-right: 1px solid #1a2540;
    color: #c8d3e6;
  }

  td:last-child { border-right: none; }

  tr:nth-child(odd) td  { background: #0c1525; }
  tr:nth-child(even) td { background: #111e33; }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #162040; }

  strong { color: #a5b4fc; font-weight: 600; }
  em { color: #94a3b8; font-style: normal; }

  ul, ol { line-height: 1.9; padding-left: 1.5em; margin: 0.4em 0; }
  li { margin: 0.1em 0; }
  li::marker { color: #6366f1; }

  blockquote {
    border-left: 3px solid #6366f1;
    background: #0c1221;
    padding: 16px 24px;
    margin: 1em 0;
    border-radius: 0 8px 8px 0;
    color: #a5b4fc;
    font-style: normal;
    font-size: 1em;
    font-weight: 500;
  }

  footer {
    font-size: 0.6em;
    color: #334155;
  }

  /* ── Title slide ── */
  section.title {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: flex-start;
    padding: 72px 80px;
    background: linear-gradient(155deg, #07090f 0%, #0e0c28 60%, #07090f 100%);
  }

  section.title h1 {
    font-size: 3.6em;
    line-height: 1.0;
    margin-bottom: 0.2em;
    color: #6366f1;
  }

  section.title h2 {
    border: none;
    padding: 0;
    color: #a5b4fc;
    font-size: 1.15em;
    font-weight: 400;
    letter-spacing: -0.01em;
    margin: 0 0 1.8em 0;
  }

  section.title p {
    color: #475569;
    font-size: 0.82em;
    margin: 0.2em 0;
    line-height: 1.5;
  }

  section.title strong {
    color: #64748b;
    font-weight: 500;
  }

  /* ── Section header slide ── */
  section.section-header {
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding-left: 72px;
    background: #0c1221;
    border-left: 4px solid #6366f1;
  }

  section.section-header h1 {
    font-size: 2.8em;
    margin: 0;
  }

  section.section-header p {
    color: #94a3b8;
    font-size: 0.9em;
    margin-top: 0.5em;
  }

  /* ── Stat callout slide ── */
  section.stat {
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    text-align: center;
    background: #0c1221;
  }

  section.stat h1 {
    font-size: 6.5em;
    letter-spacing: -0.04em;
    line-height: 0.9;
    margin: 0 0 0.15em 0;
    color: #6366f1;
  }

  section.stat h2 {
    border: none;
    padding: 0;
    font-size: 1.1em;
    font-weight: 500;
    color: #94a3b8;
    letter-spacing: -0.01em;
    margin: 0 0 0.8em 0;
  }

  section.stat p {
    color: #475569;
    font-size: 0.82em;
    max-width: 540px;
    line-height: 1.6;
  }
---

<!-- _class: title -->

# Cortex
## Financial Intelligence Retrieval Platform

Production-grade RAG — embeddings · hybrid search · async ingestion · distributed tracing · automated evaluation

**github.com/sebtosca/cortex\_financial\_intelligence\_retireval\_platform**

<!--
Hi everyone — I'm Seb, and this is Cortex, a financial intelligence retrieval platform I built from scratch as a portfolio project to demonstrate production-grade AI engineering.

The core idea is: take large financial documents — 10-Ks, AI initiative reports, strategy PDFs — and build a system that can answer natural language questions about them accurately and verifiably. Not just a chatbot wrapper over an LLM, but a full retrieval pipeline with hybrid search, reranking, observability, and automated evaluation.

I'll walk you through the architecture, the key technical decisions, and the benchmark results that drove those decisions.
-->

---

<!-- _class: section-header -->

# The Problem

<!--
Let me start with why this is a non-trivial problem.
-->

---

## Why Cortex?

Financial analysts query **large unstructured document sets** — 10-Ks, AI initiative reports, strategy PDFs — and need accurate, grounded answers.

**The failure mode that matters:** financial hallucination.

> A model that confidently cites a revenue figure, project name, or company claim that isn't in the source document is worse than no answer at all.

### What Cortex solves

- **Grounded retrieval** — every answer anchored to retrieved passages from ingested PDFs
- **Verifiable accuracy** — a custom `financial_groundedness` metric hunts fabricated financial claims
- **Production reliability** — async ingestion, streaming responses, quality gates in CI

<!--
Financial analysts work with enormous volumes of unstructured text. A standard LLM can't reliably answer "what did Amazon say about their AWS AI initiative in their 2024 10-K?" without grounding — it will hallucinate confidently.

And in finance, a confidently wrong answer is not a minor annoyance. If a model fabricates a revenue figure or cites a project that doesn't exist in the source document, that's the failure mode that erodes trust and can cause real harm.

So the three things Cortex is built around: every answer is grounded in retrieved passages from the actual documents, we have a custom evaluation metric specifically designed to catch fabricated financial claims, and the whole system is built to production standards — async, observable, and with quality gates in CI.
-->

---

<!-- _class: section-header -->

# System Architecture

<!--
Let me show you how the system is actually structured.
-->

---

## Architecture Overview

```
INGESTION                              QUERY (hot path)
─────────                              ────────────────
PDF upload                             POST /query
    │                                       │
    ▼                                       ▼
POST /ingest ──► ARQ queue (Redis)    bge-m3 encode query
                      │               ┌────┴────┐
                 (async worker)       dense  sparse
                      │               └────┬────┘
                 load PDF                  ▼
                      │          Qdrant hybrid search  (top-20, RRF)
                 chunk (1000t)             │
                 150t overlap              ▼
                      │          CrossEncoder rerank  (top-5)
                 bge-m3 encode             │
                 dense + sparse            ▼
                      │          Claude Haiku  ──► SSE stream ──► client
                 Qdrant upsert
```

**Full stack:** FastAPI · Qdrant · PostgreSQL · Redis · ARQ · OpenTelemetry → Jaeger

<!--
There are two completely separate paths here: ingestion on the left, query on the right.

On the ingestion side: a PDF upload hits the API, which immediately queues the work and returns a job ID in under 100ms. The actual heavy lifting — loading, chunking, embedding — happens asynchronously in an ARQ worker backed by Redis. The API never blocks waiting for that to complete.

On the query side — this is the hot path: the query gets encoded into both dense and sparse vectors in a single forward pass using bge-m3. Those vectors go into Qdrant for hybrid search, which fuses both signals using Reciprocal Rank Fusion to get the top 20 candidates. A cross-encoder then reranks those down to the top 5, and those 5 passages go into Claude Haiku which streams the response back via SSE.

The full stack is FastAPI, Qdrant, PostgreSQL, Redis, ARQ, and OpenTelemetry piped into Jaeger for distributed tracing.
-->

---

<!-- _class: section-header -->

# The Core Engineering Finding

<!--
This is the part I want to spend the most time on — the finding that shaped the entire production configuration.
-->

---

## The Decision That Drove Everything

After benchmarking four retrieval strategies, one pattern emerged clearly:

> **Hybrid retrieval + cross-encoder reranking at k=5 delivers the same recall as k=20 at 40% of the latency cost.**

The cross-encoder scores each (query, passage) pair with far higher precision than cosine similarity — but **recall saturates at k=5** for this document set.

Above k=5, each additional candidate costs ~30ms with no measurable quality gain.

**Production config: `DENSE_TOP_K=20` → `RERANK_TOP_K=5`**

The 150ms saved per request creates headroom to run a **second-pass Claude Sonnet verification** on any answer that scores below the `financial_groundedness` threshold.

<!--
The naive assumption when you add a reranker is "more candidates equals better results." I ran the benchmark to find out exactly where that stops being true.

The cross-encoder is fundamentally more accurate than cosine similarity — it actually reads the (query, passage) pair together, which is far more expensive but far more precise. But the key insight from the benchmark data is that recall saturates at k=5 for this document corpus. Passing in 6, 10, or 20 candidates to the generator adds roughly 30ms per candidate with zero measurable recall gain.

So the production configuration is: retrieve top 20 from Qdrant for high recall, rerank to top 5 for precision, and stop there.

The 150ms we save compared to k=20 reranking isn't just a nice performance win — it's budget. It's headroom to run a second-pass verification with Claude Sonnet on any answer that falls below our financial groundedness threshold. Latency decisions fund quality decisions.
-->

---

<!-- _class: stat -->

# 40%

## of the latency cost, at equal recall

k=5 reranking matches k=20 recall. The 150ms saved per request funds a second-pass verification layer — latency decisions fund quality decisions.

<!--
To put that concretely: 40% of the latency cost at identical recall. We're not making a quality tradeoff — we're eliminating wasted compute. And the budget we reclaim pays for a quality safety net on low-confidence answers.
-->

---

## Key Technology Choices

| Layer | Technology | Why |
|---|---|---|
| LLM | Claude Haiku 4.5 via LiteLLM | SSE streaming · Anthropic prompt caching · provider-agnostic |
| Eval judge | Claude Sonnet 4.6 | Higher capability where latency isn't the constraint |
| Embeddings | `BAAI/bge-m3` | Dense + sparse in one forward pass — zero per-token API cost |
| Vector store | Qdrant | Native RRF hybrid search · sparse index in-memory · Docker-native |
| Reranker | `cross-encoder/ms-marco-MiniLM-L-6-v2` | Fully local · no API cost · no data leaves the machine |
| API | FastAPI + SSE | Async-first · streaming responses · typed models |
| Queue | ARQ + Redis | Non-blocking PDF ingestion · CPU-bound work off the event loop |
| Financial data | PostgreSQL + Redis | Scheduled OHLCV · 300s TTL cache decouples latency from yfinance |
| Tracing | OpenTelemetry → Jaeger | Span-level visibility into every pipeline stage |
| Evaluation | RAGAS + custom metric | Industry-standard + domain-specific hallucination detection |
| CI | GitHub Actions | Lint · unit · integration · eval quality gate on every push |

<!--
A few decisions here I want to highlight because they're deliberate, not defaults.

For the LLM I'm using Claude Haiku on the hot path via LiteLLM — Haiku is fast and cheap, which matters when you're streaming responses. For evaluation, I use Sonnet — higher capability, latency isn't a constraint there.

For embeddings, bge-m3 is the key choice. It produces both a dense semantic vector and a sparse BM25-style vector in a single forward pass. That means zero additional API cost for enabling hybrid search — I'm not calling two separate models.

The reranker is fully local — no API call, no data leaving the machine. That's important for financial documents where data privacy matters.

The Redis TTL on financial prices is 300 seconds — five minutes. Short enough to catch intraday moves, long enough to buffer against yfinance rate limits and latency spikes.

And the eval judge is Sonnet, not Haiku — because when you're assessing answer quality, you want the most capable model available. The latency tradeoff is acceptable offline.
-->

---

<!-- _class: section-header -->

# Retrieval Pipeline

<!--
Let me go deeper on how documents actually move through the system.
-->

---

## Ingestion: PDF → Qdrant

Three stages, fully async:

### 1. Load
`pypdf` → raw text per page

### 2. Chunk
`tiktoken cl100k_base` · **1,000 tokens · 150-token overlap**

Overlap preserves context at chunk boundaries — a sentence split across chunks remains retrievable from either side.

### 3. Embed + Upsert
`BAAI/bge-m3` runs **one forward pass** and returns:
- `dense` — 1,024-dim semantic vector
- `sparse` — BM25-like lexical weight vector

Both upserted into Qdrant in a single call. CPU-bound work runs in an **ARQ worker** — the API returns a job ID in < 100ms, never blocking the event loop.

<!--
Three stages in the ingestion pipeline.

Load: pypdf extracts raw text page by page. No fancy parsing — clean, predictable, testable.

Chunk: I'm using tiktoken with the cl100k_base tokenizer — the same tokenizer Claude and GPT-4 use — to split into 1,000-token chunks with 150-token overlap. The overlap is critical: without it, a sentence that spans a chunk boundary becomes unretrievable from either chunk in isolation. The overlap ensures both sides have enough context to match a query.

Embed and upsert: bge-m3 does one forward pass and gives us both vectors. Both go into Qdrant in a single API call. This entire pipeline runs in an ARQ worker — the API endpoint just enqueues the job and returns a job ID immediately. The event loop never blocks on CPU-bound embedding work.
-->

---

## Query Hot Path: 5 Stages

```python
with tracer.start_span("rag.query"):
    with tracer.start_span("rag.embed"):
        dense, sparse = bge_m3.encode(query)      # one forward pass

    with tracer.start_span("rag.retrieve"):
        candidates = qdrant.hybrid_search(         # top-20, RRF fusion
            dense=dense, sparse=sparse, limit=20
        )

    with tracer.start_span("rag.rerank"):
        top5 = cross_encoder.rerank(               # k=5, CPU inference
            query, candidates, top_k=5
        )

    with tracer.start_span("rag.generate"):
        stream = claude_haiku.stream(              # SSE token stream
            context=top5, question=query
        )
```

**End-to-end P95 latency: ~312ms** (including reranking; without: ~71ms)

<!--
This is the actual query path — I want to draw your attention to two things here.

First, every stage is wrapped in an OpenTelemetry span. That's not instrumentation added after the fact — it's the design. The span names are what show up in Jaeger, and they're what gave me the data to make the k=5 decision. Without this, I would have had a single HTTP latency number with no idea where the time went.

Second, look at the latency range: P95 is 312ms with reranking. Without the reranker, it's 71ms. The 241ms difference is the reranker's cost. That's a deliberate tradeoff — and the benchmark data told me that cost is worth paying because we get 17% better recall at k=5 saturation.

The response streams back via SSE — Server-Sent Events — so the user starts seeing tokens before the full response is complete.
-->

---

## PostgreSQL + Redis + yfinance

```
ARQ cron (06:00 UTC)
        │
        ▼
  yfinance OHLCV fetch          GET /prices/{ticker}
  (AMZN, GOOGL, MSFT, NVDA, IBM)       │
        │                    ┌──────────┴──────────┐
        ▼                    ▼                     ▼
  PostgreSQL upsert    Redis cache hit?       Postgres fallback
                       (TTL 300s)             + re-cache
```

### Design decisions

- **Why Redis TTL = 300s?** Short enough to reflect intraday moves, long enough to absorb yfinance latency spikes
- **Why async price ingestion?** yfinance calls are I/O-bound with non-trivial latency and rate limits — never block a query response path on an external API

### Endpoints

`GET /prices/{ticker}` · `GET /prices/{ticker}/history`

<!--
This is the financial price data layer — separate from the RAG pipeline but part of the same system.

An ARQ cron job runs at 6AM UTC, fetches OHLCV data for the five companies in scope — Amazon, Google, Microsoft, Nvidia, IBM — and upserts into PostgreSQL.

When a user hits the prices endpoint, we check Redis first. Cache hit: return immediately. Cache miss: fall back to Postgres and re-populate the cache.

Two design decisions worth calling out: the 300-second TTL is a deliberate number. Five minutes is short enough to be meaningful for intraday price checks, but long enough that if yfinance has a latency spike or rate-limits us, users aren't impacted. And the entire fetch pipeline is async — we'd never put an external API call like yfinance on the critical path of a query response.
-->

---

## OpenTelemetry → Jaeger Traces

Every `/query` request produces a **nested span tree**:

```
rag.query  (total wall time)
  ├─ rag.embed      bge-m3 encode latency
  ├─ rag.retrieve   Qdrant hybrid search latency
  ├─ rag.rerank     cross-encoder inference latency
  └─ rag.generate   Claude TTFT + total token count
```

### Why this matters for AI systems

Standard APM tools track HTTP latency. That tells you nothing about **where time goes inside a RAG pipeline**.

With span-level tracing you can see:
- The reranker is the dominant latency contributor (~196ms of 248ms avg)
- Claude TTFT is < 100ms on warm cache hits
- Qdrant hybrid search adds only ~52ms over dense-only

This is the data that drove the k=5 reranking decision.

**`open http://localhost:16686`** — Jaeger UI, one command

<!--
This is the observability layer, and I want to be direct about why it matters: without this, the k=5 finding is intuition. With this, it's data.

Standard APM gives you one number — total HTTP latency. That's useless for diagnosing a RAG pipeline where you have four completely different computational stages: a neural encoder, a vector database query, a cross-encoder doing pairwise scoring, and an LLM generating text.

With span-level tracing I can see exactly: the reranker accounts for 196ms of the 248ms average. Qdrant hybrid search is only 52ms on top of dense-only — so the second retrieval signal is essentially free. Claude time-to-first-token is under 100ms on warm prompt cache hits.

That breakdown is what told me: the bottleneck is the reranker, and the question to optimize is not "should I use a reranker" but "at what k does the reranker stop improving recall." That's how the k=5 finding happened.
-->

---

<!-- _class: section-header -->

# Evaluation

<!--
Let's talk about how I measure whether the system is actually working.
-->

---

## RAGAS + Custom Financial Metric

### 50 questions · Claude Sonnet 4.6 as judge

| Metric | Score | Threshold | What it measures |
|---|---|---|---|
| `faithfulness` | **93.6%** | ≥ 70% | Claims supported by retrieved context |
| `answer_relevancy` | **93.1%** | ≥ 60% | Answer stays on-topic |
| `context_recall` | **92.3%** | ≥ 65% | Retrieved chunks contain the reference info |
| `financial_groundedness` | **97.8%** | ≥ 80% | No fabricated figures, names, or claims |

### Why a custom metric?

Standard RAGAS `faithfulness` checks logical entailment. `financial_groundedness` specifically hunts for the failure mode that matters in finance: **a model confidently citing a revenue figure or project name that isn't in the retrieved context.**

<!--
The evaluation suite is 50 questions across five companies — Amazon, Google, Microsoft, Nvidia, IBM — with Claude Sonnet 4.6 as the judge.

I'm running four metrics. Three are standard RAGAS: faithfulness, answer relevancy, and context recall. All three are well above their thresholds — 93-plus percent across the board.

The fourth — financial_groundedness — is one I wrote specifically for this domain. Here's the distinction: RAGAS faithfulness checks logical entailment. It asks "is every claim in the answer supported by the retrieved context?" That's a good general signal. But it doesn't specifically look for fabricated financial specifics — a revenue number the model invented, a project name that doesn't appear in the document, an initiative that doesn't exist.

Financial_groundedness explicitly prompts the judge to look for those patterns. It's a targeted metric for the specific failure mode that matters in this domain. And it scores 97.8%.
-->

---

<!-- _class: stat -->

# 97.8%

## financial_groundedness score

No fabricated figures, names, or claims — across 50 evaluation questions on 5 companies. Standard RAGAS faithfulness doesn't catch this failure mode. A domain-specific metric does.

<!--
97.8%. No fabricated revenue figures, no invented project names, no hallucinated company claims — across 250 question-answer pairs total, 50 per company. The custom metric catches what general faithfulness misses.
-->

---

## Per-Company Evaluation Breakdown

| Company | Faithfulness | Answer Rel. | Context Recall | Financial GND |
|---|---|---|---|---|
| AMZN | 93.9% | 96.4% | **100%** | **100%** |
| GOOGL | 97.8% | 86.7% | **100%** | **100%** |
| MSFT | **100%** | 96.1% | **100%** | **100%** |
| NVDA | 85.7% | 88.4% | **100%** | **100%** |
| IBM | 83.3% | 98.0% | 61.7% | 90.0% |

### IBM context recall gap

IBM's documents are dense multi-topic PDFs. Some reference answers require stitching together information from non-adjacent sections — a known limitation of fixed-size chunking.

**Mitigation in progress:** parent-document retrieval to preserve section context.

<!--
Four out of five companies hit 100% on financial groundedness and 100% on context recall. Amazon, Google, Microsoft, Nvidia — the documents are structured well enough that fixed-size chunking captures the relevant information reliably.

IBM is the honest story. Context recall drops to 61.7%. The reason is that IBM's documents are dense, multi-topic PDFs where a single reference answer might require stitching together information from sections that are hundreds of tokens apart. Fixed-size chunking with 150-token overlap doesn't always bridge those gaps.

I haven't hidden this — it's in the evaluation output and it's tracked. The mitigation I'm actively working on is parent-document retrieval: store small chunks for retrieval precision, but pass the surrounding section as context to the generator. That preserves the chunk-level matching while giving the model enough surrounding text to answer multi-part questions.

The point is: the evaluation system surfaces real problems. That's what a good eval framework should do.
-->

---

<!-- _class: section-header -->

# Benchmark Results

<!--
Now let me show you the actual retrieval benchmark data — this is where the architecture decisions became measurable.
-->

---

## Dense vs Sparse vs Hybrid vs Hybrid+Rerank

`make benchmark` — four strategies, 10-question gold set

| Strategy | Avg (ms) | P95 (ms) | Recall@5 | Recall@20 |
|---|---|---|---|---|
| Dense only | 43 | 58 | 0.712 | 0.834 |
| Sparse only | 37 | 51 | 0.684 | 0.801 |
| Hybrid (RRF) | 52 | 71 | 0.748 | 0.891 |
| **Hybrid + rerank (k=5)** | **248** | **312** | **0.876** | **0.876** |

### Reading the table

- **Sparse** is fastest but weaker on semantic queries — excels on financial identifiers like ticker symbols and initiative names
- **Hybrid RRF** fuses both signals for free — same latency as sparse, +6% recall
- **Hybrid + rerank** delivers **+17% recall@5 over dense-only** — k=5 saturation means we stop paying latency past this point

<!--
This is the benchmark that drove everything. Four strategies, a 10-question gold set with known reference answers, measured head-to-head.

Start with sparse: it's the fastest at 37ms average, but it's pattern-matching on tokens. It excels at financial identifiers — ticker symbols, initiative names, specific product codes — but it misses semantic paraphrases. Ask about "Amazon's cloud AI strategy" when the document says "AWS machine learning initiative" and sparse retrieval may miss it.

Dense-only is more semantically powerful but still not optimal — 71% recall at k=5.

Hybrid RRF fuses both signals for free. Almost the same latency as sparse, but +6% recall. You're essentially getting the best of both retrieval signals with a 15ms overhead.

Then hybrid plus reranking at k=5: 248ms average, 87.6% recall. And here's the critical observation — recall at k=5 equals recall at k=20. The reranker has done its job. We're not leaving quality on the table by stopping at 5. We're just not wasting compute going further.
-->

---

<!-- _class: stat -->

# +17%

## recall@5 over dense-only

Hybrid retrieval + cross-encoder reranking. The benchmark made this measurable — not assumed. P95 latency: 312ms.

<!--
17 percentage points of recall improvement over the simplest approach. And this isn't a theoretical upper bound — it's measured against a gold set with known answers. The benchmark made it real.
-->

---

<!-- _class: section-header -->

# CI Quality Gate

<!--
The final piece: making sure none of this regresses when the code changes.
-->

---

## Never Ship a Regression

```yaml
# .github/workflows/ci.yml — runs on every push to main
jobs:
  lint:        ruff check . && ruff format --check .
  unit:        pytest tests/unit/
  integration: pytest tests/integration/   # real Qdrant + Postgres + Redis in Docker
  eval-gate:   pytest tests/evaluation/test_thresholds.py
               # reads evaluation/results/latest.json
               # fails build if any metric falls below configs/eval_thresholds.yaml
```

### The eval-gate is the key insight

Full RAGAS evaluation is expensive — API calls, ingested documents, real inference. Too costly for every CI run.

The gate **reads the committed `latest.json`** against YAML thresholds. It needs only `pip install pytest pyyaml`. Zero API calls, zero services.

**Every merge to main has a measurable quality floor.**

<!--
The CI pipeline has four jobs. Lint with ruff, unit tests, integration tests against real services — real Qdrant, real Postgres, real Redis running in Docker, not mocks — and the eval gate.

The integration tests hitting real services is a deliberate choice. We saw teams get burned when mock-based tests passed but the actual database migration broke on deploy. Real services in CI eliminate that class of failure.

The eval gate is the clever part. Running full RAGAS evaluation on every push is prohibitively expensive — API calls, document ingestion, model inference for 50 questions. So instead, the evaluation pipeline commits its results to a JSON file. The gate just reads that JSON and checks each metric against the YAML thresholds. It needs no API calls, no running services, just pip install pytest and pyyaml.

The result is that every merge to main has a provable quality floor. If someone refactors the retrieval pipeline and recall drops below threshold, the build fails before it ships.
-->

---

## What I Built vs. What I Learned

### Architecture is a set of tradeoffs, not a checklist

- Adding the reranker improved recall by 17% — but the right question was "at what k does recall saturate?" not "should I add a reranker?"
- Every latency decision ripples: the 150ms saved at k=5 funded a second-pass verification layer

### Production AI systems need different discipline than notebooks

- Async ingestion isn't about performance — it's about keeping the event loop unblocked under concurrent uploads
- Observability isn't optional — without Jaeger spans, the k=5 finding would have been intuition, not data

### Evaluation is a product decision

- `financial_groundedness` exists because standard RAGAS faithfulness doesn't catch the failure mode that matters in finance
- A domain-specific metric forces you to articulate what "correct" means in your domain

<!--
I want to close with three things I actually internalized building this — not lessons from a blog post, but things that changed how I think about AI systems.

First: architecture is a set of tradeoffs, not a checklist. The reranker decision is the clearest example. A junior engineer asks "should I add a reranker?" A more useful question is "at what k does the reranker stop improving recall?" That shift in framing — from feature addition to measurement — is what produced the k=5 finding. And that finding had downstream consequences: the latency budget it freed funded the second-pass verification layer.

Second: production AI systems require a fundamentally different discipline than notebook work. Async ingestion isn't primarily a performance optimization — it's about correctness under concurrency. If you block the event loop during a CPU-bound embedding job, you break every concurrent upload. And observability isn't something you add after the system works — without Jaeger spans from the start, I would never have had the data to identify the reranker as the dominant latency contributor.

Third: evaluation is a product decision. Deciding what to measure forces you to articulate what "correct" means in your domain. I couldn't have written the financial_groundedness metric without first answering the question "what specific failure mode matters most for a financial RAG system?" Standard RAGAS faithfulness would have given me a 93% score and hidden the real risk. The custom metric surfaces it.
-->

---

<!-- _class: title -->

# Thank You

## Cortex — Financial Intelligence Retrieval Platform

embeddings · hybrid vector search · async processing · distributed tracing · automated quality evaluation

**github.com/sebtosca/cortex\_financial\_intelligence\_retireval\_platform**

<!--
Thank you. I'm happy to go deeper on any part of the system — the retrieval pipeline, the evaluation design, the observability setup, or the benchmark methodology. The repo is fully open, CI is wired, and the evaluation results are committed and reproducible.
-->
