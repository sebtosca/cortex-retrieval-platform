from __future__ import annotations

from ingestion.models import Chunk
from .models import EmbeddedChunk

_MODEL_NAME = "BAAI/bge-m3"


class BGEM3Embedder:
    """Lazy-loading wrapper around BAAI/bge-m3.

    The ~2GB model is only loaded on the first call to encode().
    All subsequent calls reuse the loaded instance.
    """

    def __init__(self, use_fp16: bool = True, batch_size: int = 8):
        self._use_fp16 = use_fp16
        self._batch_size = batch_size
        self._model = None  # loaded on first use

    def _load(self):
        if self._model is None:
            from FlagEmbedding import BGEM3FlagModel
            self._model = BGEM3FlagModel(_MODEL_NAME, use_fp16=self._use_fp16)

    def encode_texts(self, texts: list[str]) -> tuple[list[list[float]], list[dict]]:
        """Return (dense_vectors, sparse_lexical_weights) for a list of texts."""
        self._load()
        output = self._model.encode(
            texts,
            return_dense=True,
            return_sparse=True,
            return_colbert_vecs=False,
            batch_size=self._batch_size,
        )
        dense = [v.tolist() for v in output["dense_vecs"]]
        sparse = output["lexical_weights"]
        return dense, sparse

    def embed_chunks(self, chunks: list[Chunk]) -> list[EmbeddedChunk]:
        texts = [c.text for c in chunks]
        dense_vecs, sparse_vecs = self.encode_texts(texts)

        results = []
        for chunk, dvec, sw in zip(chunks, dense_vecs, sparse_vecs):
            indices = [int(k) for k in sw.keys()]
            values = [float(v) for v in sw.values()]
            results.append(EmbeddedChunk(
                chunk=chunk,
                dense_vector=dvec,
                sparse_indices=indices,
                sparse_values=values,
            ))
        return results
