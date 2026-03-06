import uuid
import logging
from concurrent.futures import ThreadPoolExecutor
from fastapi import APIRouter, BackgroundTasks, HTTPException

from app.src.pipeline.runner import run_pipeline
from .models import JobRequest, JobResponse
from app.src.db import create_job, get_job, list_jobs, load_checkpoint, STAGE_ORDER


logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)


_executor = ThreadPoolExecutor(max_workers=1)

router = APIRouter()


@router.post("/jobs", response_model=JobResponse, status_code=201)
def submit_job(req: JobRequest, background_tasks: BackgroundTasks):
    """Create a new job and start the pipeline in the background."""
    job_id = str(uuid.uuid4())
    create_job(job_id, req.query, req.word_count)
    background_tasks.add_task(_executor.submit, run_pipeline, job_id)
    return get_job(job_id)


@router.post("/jobs/{job_id}/resume", response_model=JobResponse)
def resume_job(job_id: str, background_tasks: BackgroundTasks):
    """
    Replay the pipeline from the last successful checkpoint.
    Safe to call on any non-running job.
    """
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] not in ("FAILED", "PENDING", "ARTICLE_GENERATED"):
        raise HTTPException(409, f"Job is currently in state '{job['status']}' — wait before resuming")
    background_tasks.add_task(_executor.submit, run_pipeline, job_id)
    return get_job(job_id)


@router.get("/jobs/{job_id}", response_model=JobResponse)
def job_status(job_id: str):
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return job


@router.get("/jobs/{job_id}/result")
def job_result(job_id: str):
    """Return the final article payload once the job is complete."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    if job["status"] != "ARTICLE_GENERATED":
        raise HTTPException(409, f"Job not complete yet — current status: {job['status']}")
    return load_checkpoint(job_id, "ARTICLE_GENERATED")


@router.get("/jobs/{job_id}/checkpoint/{stage}")
def get_checkpoint(job_id: str, stage: str):
    """Inspect any intermediate checkpoint for debugging."""
    
    if stage not in STAGE_ORDER:
        raise HTTPException(400, f"Unknown stage. Valid stages: {STAGE_ORDER}")
    data = load_checkpoint(job_id, stage)
    if data is None:
        raise HTTPException(404, f"No checkpoint for stage '{stage}'")
    return data


@router.get("/jobs", response_model=list[JobResponse])
def get_all_jobs():
    return list_jobs()
