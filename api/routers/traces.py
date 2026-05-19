from __future__ import annotations

from fastapi import APIRouter
from fastapi.responses import RedirectResponse

router = APIRouter()


@router.get("/traces")
async def traces():
    return RedirectResponse(url="http://localhost:16686")
