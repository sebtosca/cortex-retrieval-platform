from __future__ import annotations

from .models import SearchResult

_MODEL_NAME = "cross-encoder/ms-marco-MiniLM-L-6-v2"


class CrossEncoderReranker:
    """Lazy-loading cross-encoder reranker."""

    def __init__(self, model_name: str = _MODEL_NAME):
        self._model_name = model_name
        self._model = None

    def _load(self):
        if self._model is None:
            from sentence_transformers import CrossEncoder
            self._model = CrossEncoder(self._model_name)

    def rerank(self, query: str, results: list[SearchResult], top_k: int) -> list[SearchResult]:
        if not results:
            return []

        self._load()
        pairs = [(query, r.text) for r in results]
        scores = self._model.predict(pairs)

        ranked = sorted(
            zip(scores, results),
            key=lambda x: x[0],
            reverse=True,
        )

        return [
            SearchResult(
                chunk_id=r.chunk_id,
                text=r.text,
                score=float(score),
                source=r.source,
            )
            for score, r in ranked[:top_k]
        ]
