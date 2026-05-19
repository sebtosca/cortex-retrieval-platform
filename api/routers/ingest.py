from __future__ import annotations

import logging
import uuid

from arq.connections import ArqRedis
from arq.jobs import Job, JobStatus
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile

from api.deps import get_arq_pool

router = APIRouter()
logger = logging.getLogger(__name__)

_STATUS_MAP = {
    JobStatus.queued: "queued",
    JobStatus.deferred: "queued",
    JobStatus.in_progress: "processing",
    JobStatus.complete: "complete",
}


@router.post("/ingest")
async def ingest(
    file: UploadFile = File(...),
    arq_pool: ArqRedis = Depends(get_arq_pool),
):
    job_id = str(uuid.uuid4())
    file_bytes = await file.read()
    await arq_pool.enqueue_job("run_ingestion", job_id, file_bytes, _job_id=job_id)
    return {"job_id": job_id}


@router.get("/ingest/{job_id}/status")
async def ingest_status(
    job_id: str,
    arq_pool: ArqRedis = Depends(get_arq_pool),
):
    job = Job(job_id, arq_pool)
    status = await job.status()

    if status == JobStatus.not_found:
        raise HTTPException(status_code=404, detail="Job not found")

    if status == JobStatus.complete:
        result_info = await job.result_info()
        if result_info and not result_info.success:
            return {"job_id": job_id, "status": "failed"}

    return {"job_id": job_id, "status": _STATUS_MAP.get(status, "queued")}
