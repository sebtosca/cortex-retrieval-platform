from unittest.mock import MagicMock
from retrieval.models import SearchResult
from retrieval.reranker import CrossEncoderReranker


def _results(texts: list[str]) -> list[SearchResult]:
    return [SearchResult(chunk_id=i, text=t, score=0.5) for i, t in enumerate(texts)]


def test_rerank_returns_top_k_results():
    reranker = CrossEncoderReranker()
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.9, 0.3, 0.7, 0.1, 0.5]
    reranker._model = mock_model

    results = _results(["a", "b", "c", "d", "e"])
    top = reranker.rerank("query", results, top_k=3)

    assert len(top) == 3


def test_rerank_orders_by_score_descending():
    reranker = CrossEncoderReranker()
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.2, 0.9, 0.5]
    reranker._model = mock_model

    results = _results(["low", "high", "mid"])
    top = reranker.rerank("query", results, top_k=3)

    assert top[0].text == "high"
    assert top[1].text == "mid"
    assert top[2].text == "low"


def test_rerank_score_is_cross_encoder_score():
    reranker = CrossEncoderReranker()
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.85, 0.4]
    reranker._model = mock_model

    results = _results(["best", "worst"])
    top = reranker.rerank("q", results, top_k=2)

    assert abs(top[0].score - 0.85) < 1e-6


def test_rerank_empty_input_returns_empty():
    reranker = CrossEncoderReranker()
    assert reranker.rerank("query", [], top_k=5) == []


def test_rerank_top_k_larger_than_results_returns_all():
    reranker = CrossEncoderReranker()
    mock_model = MagicMock()
    mock_model.predict.return_value = [0.9, 0.5]
    reranker._model = mock_model

    results = _results(["a", "b"])
    top = reranker.rerank("query", results, top_k=10)

    assert len(top) == 2
