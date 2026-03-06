import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, HTTPException, Depends

from ably import AblyRest
from arq import ArqRedis

from app.src.utils.env import get_ably_api_key
from app.src.redis.depends import get_redis
from .models import JobRequest, JobResponse
from app.src.db import create_job, get_job, list_jobs, load_checkpoint, STAGE_ORDER, last_completed_stage


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


_executor = ThreadPoolExecutor(max_workers=1)

router = APIRouter()

@router.post("/jobs", response_model=JobResponse, status_code=201)
async def submit_job(req: JobRequest, redis: ArqRedis = Depends(get_redis)):
    """Persist the job row and enqueue a task to the ARQ worker pool."""
    job_id = str(uuid.uuid4())
    create_job(job_id, req.query, req.word_count)
    await redis.enqueue_job("pipeline_task", job_id)
    log.info("enqueued job %s", job_id)
    return get_job(job_id)


@router.post("/jobs/{job_id}/resume", response_model=JobResponse)
async def resume_job(job_id: str, redis: ArqRedis = Depends(get_redis)):
    """Re-enqueue a failed or stuck job. Pipeline skips completed stages."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] not in ("FAILED", "PENDING", "RETRYING"):
        raise HTTPException(
            409,
            f"Cannot resume a job in state '{job['status']}'. "
            "Only FAILED, RETRYING or PENDING jobs can be resumed.",
        )
    await redis.enqueue_job("pipeline_task", job_id)
    log.info("re-enqueued job %s from stage '%s'", job_id, last_completed_stage(job_id))
    return get_job(job_id)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/jobs/{job_id}/result")
def job_result(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] != "ARTICLE_GENERATED":
        raise HTTPException(409, f"Job not complete — current status: {job['status']}")
    return load_checkpoint(job_id, "ARTICLE_GENERATED")


@router.get("/jobs/{job_id}/checkpoint/{stage}")
def get_checkpoint(job_id: str, stage: str):
    if stage not in STAGE_ORDER:
        raise HTTPException(400, f"Valid stages: {STAGE_ORDER}")
    data = load_checkpoint(job_id, stage)
    if data is None:
        raise HTTPException(404, f"No checkpoint saved for stage '{stage}' yet")
    return data


@router.get("/jobs", response_model=list[JobResponse])
def get_all_jobs():
    return list_jobs()

@router.get("/ably-token")
async def ably_token():
    """
    Return a short-lived Ably token request so the frontend never sees the
    raw API key. The JS client calls this once on load.
    """
    
    ably = AblyRest(get_ably_api_key())
    token_request = await ably.auth.create_token_request_async()
    return token_request