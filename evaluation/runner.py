from __future__ import annotations

import json
import logging
import math
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

from langchain_community.embeddings import HuggingFaceEmbeddings as LCHuggingFaceEmbeddings
from ragas import EvaluationDataset, SingleTurnSample, evaluate
from ragas.llms import LangchainLLMWrapper
from ragas.metrics._answer_relevance import AnswerRelevancy
from ragas.metrics._context_recall import ContextRecall
from ragas.metrics._faithfulness import Faithfulness
from ragas.run_config import RunConfig

from configs.settings import settings
from embeddings.bgem3 import BGEM3Embedder
from evaluation.llm_adapter import LiteLLMChatAdapter
from evaluation.metrics import financial_groundedness_score
from evaluation.pipeline import run_rag_pipeline
from llm.client import CortexLLM
from retrieval.reranker import CrossEncoderReranker
from retrieval.store import QdrantStore

logger = logging.getLogger(__name__)

RESULTS_DIR = Path(__file__).parent.parent / "evaluation" / "results"
GOLD_PATH = Path(__file__).parent.parent / "tests" / "evaluation" / "gold_questions.json"


def _ragas_llm() -> LangchainLLMWrapper:
    return LangchainLLMWrapper(LiteLLMChatAdapter(model=settings.eval_model))


def _ragas_embeddings() -> LCHuggingFaceEmbeddings:
    return LCHuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")


def run_evaluation(gold_path: Path = GOLD_PATH) -> dict:
    """Run the full RAGAS evaluation suite.

    Loads gold questions, runs the RAG pipeline for each, evaluates with
    Faithfulness / AnswerRelevancy / ContextRecall (RAGAS standard), and a
    custom FinancialGroundedness judge (Claude Sonnet).  Saves results to
    ``evaluation/results/latest.json`` and returns the result dict.
    """
    gold = json.loads(gold_path.read_text())
    logger.info("Loaded %d gold questions from %s", len(gold), gold_path)

    embedder = BGEM3Embedder(use_fp16=True, batch_size=8)
    store = QdrantStore(url=settings.qdrant_url, collection=settings.qdrant_collection)
    reranker = CrossEncoderReranker()
    llm = CortexLLM(model=settings.rag_model, max_tokens=1024)

    logger.info("Running RAG pipeline …")
    samples: list[SingleTurnSample] = []
    companies: list[str] = []
    import time as _time
    for item in gold:
        answer, contexts = run_rag_pipeline(item["question"], embedder, store, reranker, llm)
        _time.sleep(2)
        samples.append(
            SingleTurnSample(
                user_input=item["question"],
                response=answer,
                retrieved_contexts=contexts,
                reference=item["reference"],
            )
        )
        companies.append(item.get("company", "unknown"))

    dataset = EvaluationDataset(samples=samples)
    ragas_llm = _ragas_llm()
    ragas_emb = _ragas_embeddings()

    logger.info("Scoring with RAGAS standard metrics …")
    result = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(llm=ragas_llm),
            AnswerRelevancy(llm=ragas_llm, embeddings=ragas_emb),
            ContextRecall(llm=ragas_llm),
        ],
        llm=ragas_llm,
        embeddings=ragas_emb,
        show_progress=True,
        raise_exceptions=False,
        allow_nest_asyncio=True,
        run_config=RunConfig(timeout=180, max_retries=10, max_wait=60, max_workers=1),
    )

    df = result.to_pandas()
    metric_cols = [col for col in df.columns if df[col].dtype.kind == "f"]
    scores: dict[str, float] = {
        col: round(float(df[col].mean()), 4) for col in metric_cols
    }

    logger.info("Scoring custom financial_groundedness …")
    _time.sleep(30)  # cooldown after RAGAS evaluation to avoid rate limits
    fg_scores: list[float] = []
    for s in samples:
        fg_scores.append(financial_groundedness_score(s.response, s.retrieved_contexts or []))
        _time.sleep(10)
    valid = [s for s in fg_scores if not math.isnan(s)]
    scores["financial_groundedness"] = round(sum(valid) / len(valid), 4) if valid else float("nan")

    # Per-company breakdown
    per_company: dict[str, dict[str, float]] = {}
    company_indices: dict[str, list[int]] = defaultdict(list)
    for i, company in enumerate(companies):
        company_indices[company].append(i)

    for company, indices in company_indices.items():
        company_scores: dict[str, float] = {}
        for col in metric_cols:
            vals = [df[col].iloc[i] for i in indices if not math.isnan(df[col].iloc[i])]
            company_scores[col] = round(sum(vals) / len(vals), 4) if vals else float("nan")
        fg_company = [fg_scores[i] for i in indices if not math.isnan(fg_scores[i])]
        company_scores["financial_groundedness"] = (
            round(sum(fg_company) / len(fg_company), 4) if fg_company else float("nan")
        )
        per_company[company] = company_scores

    output = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "rag_model": settings.rag_model,
        "eval_model": settings.eval_model,
        "n_questions": len(gold),
        "scores": scores,
        "per_company": per_company,
    }

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    out_path = RESULTS_DIR / "latest.json"
    out_path.write_text(json.dumps(output, indent=2))
    logger.info("Results saved → %s", out_path)

    _print_table(scores, per_company)
    return output


def _print_table(scores: dict[str, float], per_company: dict[str, dict[str, float]]) -> None:
    print("\n┌─────────────────────────────────┬────────┐")
    print("│ Metric                          │  Score │")
    print("├─────────────────────────────────┼────────┤")
    for name, val in scores.items():
        label = name.replace("_", " ").title()[:31]
        score_str = f"{val:.4f}" if not math.isnan(val) else "  n/a "
        print(f"│ {label:<31} │ {score_str:>6} │")
    print("└─────────────────────────────────┴────────┘")

    if per_company:
        print("\nPer-company breakdown:")
        metric_names = list(next(iter(per_company.values())).keys())
        header = f"{'Company':<10}" + "".join(f"  {m[:14]:>14}" for m in metric_names)
        print(header)
        print("-" * len(header))
        for company, company_scores in sorted(per_company.items()):
            row = f"{company:<10}"
            for m in metric_names:
                val = company_scores.get(m, float("nan"))
                row += f"  {val:>14.4f}" if not math.isnan(val) else f"  {'n/a':>14}"
            print(row)
