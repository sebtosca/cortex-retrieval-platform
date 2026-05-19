# Cortex — Presenter Notes

---

## Slide 1 — Title: Cortex / Financial Intelligence Retrieval Platform

Hi everyone — I'm Seb, and this is Cortex, a financial intelligence retrieval platform I built from scratch as a portfolio project to demonstrate production-grade AI engineering.

The core idea is: take large financial documents — 10-Ks, AI initiative reports, strategy PDFs — and build a system that can answer natural language questions about them accurately and verifiably. Not just a chatbot wrapper over an LLM, but a full retrieval pipeline with hybrid search, reranking, observability, and automated evaluation.

I'll walk you through the architecture, the key technical decisions, and the benchmark results that drove those decisions.

---

## Slide 2 — Section: The Problem

Let me start with why this is a non-trivial problem.

---

## Slide 3 — Why Cortex?

Financial analysts work with enormous volumes of unstructured text. A standard LLM can't reliably answer "what did Amazon say about their AWS AI initiative in their 2024 10-K?" without grounding — it will hallucinate confidently.

And in finance, a confidently wrong answer is not a minor annoyance. If a model fabricates a revenue figure or cites a project that doesn't exist in the source document, that's the failure mode that erodes trust and can cause real harm.

So the three things Cortex is built around: every answer is grounded in retrieved passages from the actual documents, we have a custom evaluation metric specifically designed to catch fabricated financial claims, and the whole system is built to production standards — async, observable, and with quality gates in CI.

---

## Slide 4 — Section: System Architecture

Let me show you how the system is actually structured.

---

## Slide 5 — Architecture Overview

There are two completely separate paths here: ingestion on the left, query on the right.

On the ingestion side: a PDF upload hits the API, which immediately queues the work and returns a job ID in under 100ms. The actual heavy lifting — loading, chunking, embedding — happens asynchronously in an ARQ worker backed by Redis. The API never blocks waiting for that to complete.

On the query side — this is the hot path: the query gets encoded into both dense and sparse vectors in a single forward pass using bge-m3. Those vectors go into Qdrant for hybrid search, which fuses both signals using Reciprocal Rank Fusion to get the top 20 candidates. A cross-encoder then reranks those down to the top 5, and those 5 passages go into Claude Haiku which streams the response back via SSE.

The full stack is FastAPI, Qdrant, PostgreSQL, Redis, ARQ, and OpenTelemetry piped into Jaeger for distributed tracing.

---

## Slide 6 — Section: The Core Engineering Finding

This is the part I want to spend the most time on — the finding that shaped the entire production configuration.

---

## Slide 7 — The Decision That Drove Everything

The naive assumption when you add a reranker is "more candidates equals better results." I ran the benchmark to find out exactly where that stops being true.

The cross-encoder is fundamentally more accurate than cosine similarity — it actually reads the (query, passage) pair together, which is far more expensive but far more precise. But the key insight from the benchmark data is that recall saturates at k=5 for this document corpus. Passing in 6, 10, or 20 candidates to the generator adds roughly 30ms per candidate with zero measurable recall gain.

So the production configuration is: retrieve top 20 from Qdrant for high recall, rerank to top 5 for precision, and stop there.

The 150ms we save compared to k=20 reranking isn't just a nice performance win — it's budget. It's headroom to run a second-pass verification with Claude Sonnet on any answer that falls below our financial groundedness threshold. Latency decisions fund quality decisions.

---

## Slide 8 — Stat: 40% of the latency cost, at equal recall

To put that concretely: 40% of the latency cost at identical recall. We're not making a quality tradeoff — we're eliminating wasted compute. And the budget we reclaim pays for a quality safety net on low-confidence answers.

---

## Slide 9 — Key Technology Choices

A few decisions here I want to highlight because they're deliberate, not defaults.

For the LLM I'm using Claude Haiku on the hot path via LiteLLM — Haiku is fast and cheap, which matters when you're streaming responses. For evaluation, I use Sonnet — higher capability, latency isn't a constraint there.

For embeddings, bge-m3 is the key choice. It produces both a dense semantic vector and a sparse BM25-style vector in a single forward pass. That means zero additional API cost for enabling hybrid search — I'm not calling two separate models.

The reranker is fully local — no API call, no data leaving the machine. That's important for financial documents where data privacy matters.

The Redis TTL on financial prices is 300 seconds — five minutes. Short enough to catch intraday moves, long enough to buffer against yfinance rate limits and latency spikes.

And the eval judge is Sonnet, not Haiku — because when you're assessing answer quality, you want the most capable model available. The latency tradeoff is acceptable offline.

---

## Slide 10 — Section: Retrieval Pipeline

Let me go deeper on how documents actually move through the system.

---

## Slide 11 — Ingestion: PDF → Qdrant

Three stages in the ingestion pipeline.

Load: pypdf extracts raw text page by page. No fancy parsing — clean, predictable, testable.

Chunk: I'm using tiktoken with the cl100k_base tokenizer — the same tokenizer Claude and GPT-4 use — to split into 1,000-token chunks with 150-token overlap. The overlap is critical: without it, a sentence that spans a chunk boundary becomes unretrievable from either chunk in isolation. The overlap ensures both sides have enough context to match a query.

Embed and upsert: bge-m3 does one forward pass and gives us both vectors. Both go into Qdrant in a single API call. This entire pipeline runs in an ARQ worker — the API endpoint just enqueues the job and returns a job ID immediately. The event loop never blocks on CPU-bound embedding work.

---

## Slide 12 — Query Hot Path: 5 Stages

This is the actual query path — I want to draw your attention to two things here.

First, every stage is wrapped in an OpenTelemetry span. That's not instrumentation added after the fact — it's the design. The span names are what show up in Jaeger, and they're what gave me the data to make the k=5 decision. Without this, I would have had a single HTTP latency number with no idea where the time went.

Second, look at the latency range: P95 is 312ms with reranking. Without the reranker, it's 71ms. The 241ms difference is the reranker's cost. That's a deliberate tradeoff — and the benchmark data told me that cost is worth paying because we get 17% better recall at k=5 saturation.

The response streams back via SSE — Server-Sent Events — so the user starts seeing tokens before the full response is complete.

---

## Slide 13 — PostgreSQL + Redis + yfinance

This is the financial price data layer — separate from the RAG pipeline but part of the same system.

An ARQ cron job runs at 6AM UTC, fetches OHLCV data for the five companies in scope — Amazon, Google, Microsoft, Nvidia, IBM — and upserts into PostgreSQL.

When a user hits the prices endpoint, we check Redis first. Cache hit: return immediately. Cache miss: fall back to Postgres and re-populate the cache.

Two design decisions worth calling out: the 300-second TTL is a deliberate number. Five minutes is short enough to be meaningful for intraday price checks, but long enough that if yfinance has a latency spike or rate-limits us, users aren't impacted. And the entire fetch pipeline is async — we'd never put an external API call like yfinance on the critical path of a query response.

---

## Slide 14 — OpenTelemetry → Jaeger Traces

This is the observability layer, and I want to be direct about why it matters: without this, the k=5 finding is intuition. With this, it's data.

Standard APM gives you one number — total HTTP latency. That's useless for diagnosing a RAG pipeline where you have four completely different computational stages: a neural encoder, a vector database query, a cross-encoder doing pairwise scoring, and an LLM generating text.

With span-level tracing I can see exactly: the reranker accounts for 196ms of the 248ms average. Qdrant hybrid search is only 52ms on top of dense-only — so the second retrieval signal is essentially free. Claude time-to-first-token is under 100ms on warm prompt cache hits.

That breakdown is what told me: the bottleneck is the reranker, and the question to optimize is not "should I use a reranker" but "at what k does the reranker stop improving recall." That's how the k=5 finding happened.

---

## Slide 15 — Section: Evaluation

Let's talk about how I measure whether the system is actually working.

---

## Slide 16 — RAGAS + Custom Financial Metric

The evaluation suite is 50 questions across five companies — Amazon, Google, Microsoft, Nvidia, IBM — with Claude Sonnet 4.6 as the judge.

I'm running four metrics. Three are standard RAGAS: faithfulness, answer relevancy, and context recall. All three are well above their thresholds — 93-plus percent across the board.

The fourth — financial_groundedness — is one I wrote specifically for this domain. Here's the distinction: RAGAS faithfulness checks logical entailment. It asks "is every claim in the answer supported by the retrieved context?" That's a good general signal. But it doesn't specifically look for fabricated financial specifics — a revenue number the model invented, a project name that doesn't appear in the document, an initiative that doesn't exist.

Financial_groundedness explicitly prompts the judge to look for those patterns. It's a targeted metric for the specific failure mode that matters in this domain. And it scores 97.8%.

---

## Slide 17 — Stat: 97.8% financial_groundedness

97.8%. No fabricated revenue figures, no invented project names, no hallucinated company claims — across 250 question-answer pairs total, 50 per company. The custom metric catches what general faithfulness misses.

---

## Slide 18 — Per-Company Evaluation Breakdown

Four out of five companies hit 100% on financial groundedness and 100% on context recall. Amazon, Google, Microsoft, Nvidia — the documents are structured well enough that fixed-size chunking captures the relevant information reliably.

IBM is the honest story. Context recall drops to 61.7%. The reason is that IBM's documents are dense, multi-topic PDFs where a single reference answer might require stitching together information from sections that are hundreds of tokens apart. Fixed-size chunking with 150-token overlap doesn't always bridge those gaps.

I haven't hidden this — it's in the evaluation output and it's tracked. The mitigation I'm actively working on is parent-document retrieval: store small chunks for retrieval precision, but pass the surrounding section as context to the generator. That preserves the chunk-level matching while giving the model enough surrounding text to answer multi-part questions.

The point is: the evaluation system surfaces real problems. That's what a good eval framework should do.

---

## Slide 19 — Section: Benchmark Results

Now let me show you the actual retrieval benchmark data — this is where the architecture decisions became measurable.

---

## Slide 20 — Dense vs Sparse vs Hybrid vs Hybrid+Rerank

This is the benchmark that drove everything. Four strategies, a 10-question gold set with known reference answers, measured head-to-head.

Start with sparse: it's the fastest at 37ms average, but it's pattern-matching on tokens. It excels at financial identifiers — ticker symbols, initiative names, specific product codes — but it misses semantic paraphrases. Ask about "Amazon's cloud AI strategy" when the document says "AWS machine learning initiative" and sparse retrieval may miss it.

Dense-only is more semantically powerful but still not optimal — 71% recall at k=5.

Hybrid RRF fuses both signals for free. Almost the same latency as sparse, but +6% recall. You're essentially getting the best of both retrieval signals with a 15ms overhead.

Then hybrid plus reranking at k=5: 248ms average, 87.6% recall. And here's the critical observation — recall at k=5 equals recall at k=20. The reranker has done its job. We're not leaving quality on the table by stopping at 5. We're just not wasting compute going further.

---

## Slide 21 — Stat: +17% recall@5 over dense-only

17 percentage points of recall improvement over the simplest approach. And this isn't a theoretical upper bound — it's measured against a gold set with known answers. The benchmark made it real.

---

## Slide 22 — Section: CI Quality Gate

The final piece: making sure none of this regresses when the code changes.

---

## Slide 23 — Never Ship a Regression

The CI pipeline has four jobs. Lint with ruff, unit tests, integration tests against real services — real Qdrant, real Postgres, real Redis running in Docker, not mocks — and the eval gate.

The integration tests hitting real services is a deliberate choice. We saw teams get burned when mock-based tests passed but the actual database migration broke on deploy. Real services in CI eliminate that class of failure.

The eval gate is the clever part. Running full RAGAS evaluation on every push is prohibitively expensive — API calls, document ingestion, model inference for 50 questions. So instead, the evaluation pipeline commits its results to a JSON file. The gate just reads that JSON and checks each metric against the YAML thresholds. It needs no API calls, no running services, just pip install pytest and pyyaml.

The result is that every merge to main has a provable quality floor. If someone refactors the retrieval pipeline and recall drops below threshold, the build fails before it ships.

---

## Slide 24 — What I Built vs. What I Learned

I want to close with three things I actually internalized building this — not lessons from a blog post, but things that changed how I think about AI systems.

First: architecture is a set of tradeoffs, not a checklist. The reranker decision is the clearest example. A junior engineer asks "should I add a reranker?" A more useful question is "at what k does the reranker stop improving recall?" That shift in framing — from feature addition to measurement — is what produced the k=5 finding. And that finding had downstream consequences: the latency budget it freed funded the second-pass verification layer.

Second: production AI systems require a fundamentally different discipline than notebook work. Async ingestion isn't primarily a performance optimization — it's about correctness under concurrency. If you block the event loop during a CPU-bound embedding job, you break every concurrent upload. And observability isn't something you add after the system works — without Jaeger spans from the start, I would never have had the data to identify the reranker as the dominant latency contributor.

Third: evaluation is a product decision. Deciding what to measure forces you to articulate what "correct" means in your domain. I couldn't have written the financial_groundedness metric without first answering the question "what specific failure mode matters most for a financial RAG system?" Standard RAGAS faithfulness would have given me a 93% score and hidden the real risk. The custom metric surfaces it.

---

## Slide 25 — Thank You

Thank you. I'm happy to go deeper on any part of the system — the retrieval pipeline, the evaluation design, the observability setup, or the benchmark methodology. The repo is fully open, CI is wired, and the evaluation results are committed and reproducible.
