"""RAGAS evaluation suite.

Two distinct test groups with different skip conditions:

1. ``test_evaluation_runs_*``  — full pipeline run.
   Skipped unless ANTHROPIC_API_KEY is set AND Qdrant is reachable.
   Run locally via ``make eval``.

2. ``test_*_above_threshold``  — CI regression gate.
   Reads ``evaluation/results/latest.json`` (committed to the repo) and
   checks each metric against ``configs/eval_thresholds.yaml``.
   No API key or ML stack required — safe to run on every push to main.
"""
from __future__ import annotations

import json
import math
import os
from pathlib import Path

# Load .env before the skip conditions are evaluated so that
# ANTHROPIC_API_KEY set in .env is visible to os.environ.get().
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent.parent / ".env")
except ImportError:
    pass

import pytest
import yaml

_REPO_ROOT = Path(__file__).parent.parent.parent
RESULTS_PATH = _REPO_ROOT / "evaluation" / "results" / "latest.json"
THRESHOLDS_PATH = _REPO_ROOT / "configs" / "eval_thresholds.yaml"

# ── skip conditions ────────────────────────────────────────────────────────────

needs_api_key = pytest.mark.skipif(
    not os.environ.get("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not set — configure it to run the full evaluation",
)

needs_results = pytest.mark.skipif(
    not RESULTS_PATH.exists(),
    reason="evaluation/results/latest.json missing — run `make eval` first",
)


# ── helpers ────────────────────────────────────────────────────────────────────

def _scores() -> dict[str, float]:
    return json.loads(RESULTS_PATH.read_text())["scores"]


def _threshold(metric: str) -> float:
    data = yaml.safe_load(THRESHOLDS_PATH.read_text())
    return float(data["thresholds"][metric])


# ── full evaluation run (local / scheduled CI only) ───────────────────────────

@needs_api_key
def test_evaluation_runs_and_produces_scores():
    """End-to-end: RAG pipeline → RAGAS metrics → custom judge → writes latest.json."""
    from evaluation.runner import run_evaluation

    results = run_evaluation()

    assert "scores" in results
    scores = results["scores"]
    assert len(scores) >= 3, "expected at least 3 metrics"
    for name, val in scores.items():
        assert not math.isnan(val), f"{name!r} returned NaN — check API key and Qdrant"

    assert RESULTS_PATH.exists()
    saved = json.loads(RESULTS_PATH.read_text())
    assert saved["scores"] == scores


# ── CI threshold gate (reads committed latest.json) ───────────────────────────

@needs_results
def test_faithfulness_above_threshold():
    """faithfulness must be >= configs/eval_thresholds.yaml → thresholds.faithfulness."""
    threshold = _threshold("faithfulness")
    actual = _scores().get("faithfulness", 0.0)
    assert actual >= threshold, (
        f"faithfulness {actual:.4f} is below the {threshold} threshold — "
        "retrieval/generation quality may have regressed; re-run `make eval` to investigate"
    )


@needs_results
def test_context_recall_above_threshold():
    """context_recall must be >= configs/eval_thresholds.yaml → thresholds.context_recall."""
    threshold = _threshold("context_recall")
    actual = _scores().get("context_recall", 0.0)
    assert actual >= threshold, (
        f"context_recall {actual:.4f} is below the {threshold} threshold — "
        "retrieved chunks may not cover the necessary information; check chunk size and top_k"
    )


@needs_results
def test_answer_relevancy_above_threshold():
    """answer_relevancy must be >= configs/eval_thresholds.yaml → thresholds.answer_relevancy."""
    threshold = _threshold("answer_relevancy")
    actual = _scores().get("answer_relevancy", 0.0)
    assert actual >= threshold, (
        f"answer_relevancy {actual:.4f} is below the {threshold} threshold — "
        "answers may be drifting off-topic; check the prompt template"
    )


@needs_results
def test_financial_groundedness_above_threshold():
    """financial_groundedness must be >= configs/eval_thresholds.yaml → thresholds.financial_groundedness."""
    threshold = _threshold("financial_groundedness")
    actual = _scores().get("financial_groundedness", 0.0)
    assert actual >= threshold, (
        f"financial_groundedness {actual:.4f} is below the {threshold} threshold — "
        "model may be generating unsupported financial claims; check RAG prompt or top_k"
    )
