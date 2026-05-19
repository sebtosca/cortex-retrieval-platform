from __future__ import annotations

from fastapi import APIRouter, Depends

from api.deps import get_store
from retrieval.store import QdrantStore

router = APIRouter()


@router.get("/health")
async def health(store: QdrantStore = Depends(get_store)):
    qdrant_status = "ok"
    try:
        store._client.get_collections()
    except Exception:
        qdrant_status = "error"

    return {"status": "ok", "qdrant": qdrant_status}
