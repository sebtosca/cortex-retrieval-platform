from __future__ import annotations

from embeddings.models import EmbeddedChunk
from .models import SearchResult

DENSE_DIM = 1024


class QdrantStore:
    def __init__(self, url: str, collection: str):
        from qdrant_client import QdrantClient
        self._client = QdrantClient(url=url)
        self._collection = collection

    def setup_collection(self, recreate: bool = False):
        from qdrant_client.models import (
            Distance, VectorParams, SparseVectorParams, SparseIndexParams,
        )
        existing = [c.name for c in self._client.get_collections().collections]
        if self._collection in existing:
            if recreate:
                self._client.delete_collection(self._collection)
            else:
                return

        self._client.create_collection(
            collection_name=self._collection,
            vectors_config={"dense": VectorParams(size=DENSE_DIM, distance=Distance.COSINE)},
            sparse_vectors_config={"sparse": SparseVectorParams(index=SparseIndexParams())},
        )

    def upsert(self, embedded_chunks: list[EmbeddedChunk]):
        from qdrant_client.models import PointStruct, SparseVector

        points = [
            PointStruct(
                id=ec.chunk.chunk_id,
                payload={
                    "text": ec.chunk.text,
                    "chunk_id": ec.chunk.chunk_id,
                    "doc_source": ec.chunk.doc_source,
                    "company": ec.chunk.company,
                },
                vector={
                    "dense": ec.dense_vector,
                    "sparse": SparseVector(
                        indices=ec.sparse_indices,
                        values=ec.sparse_values,
                    ),
                },
            )
            for ec in embedded_chunks
        ]
        self._client.upsert(collection_name=self._collection, points=points, wait=True)

    def dense_search(self, dense: list[float], limit: int = 20) -> list[SearchResult]:
        results = self._client.query_points(
            collection_name=self._collection,
            query=dense,
            using="dense",
            limit=limit,
        )
        return [
            SearchResult(
                chunk_id=r.payload["chunk_id"],
                text=r.payload["text"],
                score=r.score,
                source=r.payload.get("doc_source"),
            )
            for r in results.points
        ]

    def sparse_search(
        self,
        sparse_indices: list[int],
        sparse_values: list[float],
        limit: int = 20,
    ) -> list[SearchResult]:
        from qdrant_client.models import SparseVector

        results = self._client.query_points(
            collection_name=self._collection,
            query=SparseVector(indices=sparse_indices, values=sparse_values),
            using="sparse",
            limit=limit,
        )
        return [
            SearchResult(
                chunk_id=r.payload["chunk_id"],
                text=r.payload["text"],
                score=r.score,
                source=r.payload.get("doc_source"),
            )
            for r in results.points
        ]

    def hybrid_search(
        self,
        dense: list[float],
        sparse_indices: list[int],
        sparse_values: list[float],
        limit: int = 20,
    ) -> list[SearchResult]:
        from qdrant_client.models import Prefetch, FusionQuery, SparseVector

        results = self._client.query_points(
            collection_name=self._collection,
            prefetch=[
                Prefetch(query=dense, using="dense", limit=limit),
                Prefetch(
                    query=SparseVector(indices=sparse_indices, values=sparse_values),
                    using="sparse",
                    limit=limit,
                ),
            ],
            query=FusionQuery(fusion="rrf"),
            limit=limit,
        )

        return [
            SearchResult(
                chunk_id=r.payload["chunk_id"],
                text=r.payload["text"],
                score=r.score,
                source=r.payload.get("doc_source"),
            )
            for r in results.points
        ]
