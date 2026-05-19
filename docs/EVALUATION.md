# Cortex Evaluation

Cortex uses [RAGAS](https://docs.ragas.io) to measure retrieval and generation quality on a curated gold question set, plus a custom domain metric that guards against financial hallucination.

---

## Running the evaluation

```bash
# Requires ANTHROPIC_API_KEY and a running Qdrant with ingested documents
make eval
```

Results are printed to the terminal and saved to `evaluation/results/latest.json`.

---

## Gold question set

`tests/evaluation/gold_questions.json` contains **10 manually verified questions** about IBM's AI initiatives.  Each entry has:

| Field | Purpose |
|---|---|
| `question` | The user query sent to the RAG pipeline |
| `reference` | The expected answer, used by `ContextRecall` to verify that retrieved chunks cover the necessary information |

Questions were written to span IBM's core AI strategy topics — platform capabilities, open-source commitments, governance approach, hybrid cloud, partnerships, and hallucination mitigation — to stress-test retrieval breadth as well as generation faithfulness.

---

## Metrics

### Standard RAGAS metrics (LLM judge: Claude Sonnet)

| Metric | What it measures | Threshold |
|---|---|---|
| `faithfulness` | Does the generated answer contain only claims supported by the retrieved context? | ≥ 0.70 |
| `answer_relevancy` | Is the generated answer relevant to the original question? (embedding similarity) | — |
| `context_recall` | Does the retrieved context contain the information needed to answer the question? | ≥ 0.65 |

### Custom metric: `financial_groundedness`

**Judge:** Claude Sonnet (`eval_model` in settings)

**Prompt strategy:** Given the retrieved context passages and the generated answer, Claude is asked to identify any company names, financial figures, project names, dates, or factual claims in the answer that are *absent from or not inferable from* the context. It returns a structured JSON score:

```json
{"score": 1, "reason": "All claims in the answer are directly supported by the retrieved passages."}
```

**Score:** `1.0` = fully grounded, `0.0` = unsupported claim detected.  
**Aggregate:** arithmetic mean over the gold set.  
**Threshold:** ≥ 0.80

**Why a custom metric?**  
Standard RAGAS `faithfulness` checks whether each factual claim in the answer has a supporting sentence in the context.  `financial_groundedness` adds a domain-specific layer: it explicitly asks the judge to look for *financial figures, initiative names, and project claims* — the failure mode most likely to mislead a financial intelligence user.

---

## Architecture of the evaluation pipeline

```
gold_questions.json
      │
      ▼
BGEM3Embedder.encode_texts()        ← same embedder as production
      │
      ▼
QdrantStore.hybrid_search()         ← same retrieval as production
      │
      ▼
CrossEncoderReranker.rerank()       ← same reranker as production
      │
      ▼
CortexLLM.complete()                ← Claude Haiku, same prompt template
      │
      ├──► RAGAS evaluate()         ← Faithfulness, AnswerRelevancy, ContextRecall
      │         (judge: Claude Sonnet via LangchainLLMWrapper + LiteLLMChatAdapter)
      │
      └──► financial_groundedness_score()   ← direct Anthropic SDK call
                (judge: Claude Sonnet)
```

The evaluation pipeline is **identical to the production serving path** — same embedder, same retrieval config, same reranker, same prompt template — so metric regressions reliably signal real-world quality degradation.

---

## CI quality gate

The tests in `tests/evaluation/test_ragas.py` act as a regression gate:

- `test_faithfulness_above_threshold` — fails if `faithfulness < 0.70`
- `test_context_recall_above_threshold` — fails if `context_recall < 0.65`
- `test_financial_groundedness_above_threshold` — fails if `financial_groundedness < 0.80`

All three tests are **skipped automatically** when `ANTHROPIC_API_KEY` is not set, so they never block the regular unit/integration test run.  The gate is intended to run as a separate CI step (see `.github/workflows/eval-gate.yml`).

---

## Interpreting results

```json
{
  "timestamp": "2026-05-13T10:00:00+00:00",
  "rag_model": "claude-haiku-4-5-20251001",
  "eval_model": "claude-sonnet-4-6",
  "n_questions": 10,
  "scores": {
    "faithfulness": 0.8750,
    "answer_relevancy": 0.9120,
    "context_recall": 0.7300,
    "financial_groundedness": 0.9000
  }
}
```

A `context_recall` near 0.65 indicates the retrieval pipeline is missing some relevant chunks — consider increasing `dense_top_k` or improving chunking.  A `faithfulness` drop below 0.70 after a prompt change suggests the new prompt is encouraging the model to speculate beyond the retrieved evidence.
