import asyncio
import importlib
import logging
from arq import func as arq_func
from arq.connections import RedisSettings
from arq.worker import Retry

from pydantic import create_model

from app.src.config import settings
from app.src.db import (
    save_checkpoint, load_checkpoint, set_job_status,
    last_completed_stage, get_job, STAGE_ORDER,
)
from app.src.events import push_stage

from app.src.services.serper import get_serper_responses
from app.src.services.scrapper import run_scraping_pipeline
from app.src.services.prelim import run_haiku_analysis
from app.src.services.consolidator import run_consolidator
from app.src.services.writer import run_writer

from app.src.models import ContentBlueprint, PageAnalysis, ScrapedPage, SerperResponses, GeneratedArticle

MAX_TRIES   = 5
RETRY_DELAY = [30, 60, 120, 300]  


log = logging.getLogger(__name__)


model_map = {"SERP_FETCHED": SerperResponses, "PAGES_SCRAPED": ScrapedPage, "PRELIM_ANALYSES_COMPLETE": PageAnalysis, "BLUEPRINT_READY": ContentBlueprint, "ARTICLE_GENERATED": GeneratedArticle}

def _dump(obj) -> dict:
    """Serialize pydantic model to dict, embedding the class path for reconstruction."""
    if hasattr(obj, "model_dump"):
        return {
            "__model__": f"{obj.__class__.__module__}.{obj.__class__.__qualname__}",
            "__data__": obj.model_dump(),
        }
    if hasattr(obj, "dict"):   # pydantic v1
        return {
            "__model__": f"{obj.__class__.__module__}.{obj.__class__.__qualname__}",
            "__data__": obj.dict(),
        }
    if isinstance(obj, list):
        return {"__list__": [_dump(i) for i in obj]}
    if isinstance(obj, dict):
        return {k: _dump(v) for k, v in obj.items()}
    return obj


def _load(data, stage):
    """
    Reconstruct whatever pydantic model was originally dumped.
    Works on any nesting depth — no need to specify the class at call time.
    """
    if data is None:
        return None
    if isinstance(data, dict):
        model = model_map.get(stage)
        data = model.model_validate(data)
    
    return data


async def _transition(job_id: str, status: str, error: str | None = None):
    """Write to SQLite + push Ably event atomically from the worker's perspective."""
    set_job_status(job_id, status, error)
    await push_stage(job_id, status, error)

async def pipeline_task(ctx: dict, job_id: str) -> None:
    """
    ARQ task — runs the full pipeline with checkpoint-based resume.
    `ctx` is injected by ARQ and carries the redis pool if needed later.
    """
    job = get_job(job_id)
    if not job:
        log.error("job %s not found in DB", job_id)
        return

    query      = job["query"]
    word_count = job["word_count"]
    resume_from = last_completed_stage(job_id)
    start_idx   = STAGE_ORDER.index(resume_from)

    log.info("job %s — starting from after '%s'", job_id, resume_from)

    try:
        if start_idx < STAGE_ORDER.index("SERP_FETCHED"):
            log.info("job %s — SERP_FETCHED", job_id)
            # sync call → run in thread to avoid blocking the event loop
            responses = await asyncio.to_thread(get_serper_responses, query)
            save_checkpoint(job_id, "SERP_FETCHED", _dump(responses))
            await _transition(job_id, "SERP_FETCHED")
        else:
            log.info("job %s — SERP_FETCHED (cached)", job_id)
            responses = _load(load_checkpoint(job_id, "SERP_FETCHED"), "SERP_FETCHED")

        if start_idx < STAGE_ORDER.index("PAGES_SCRAPED"):
            log.info("job %s — PAGES_SCRAPED", job_id)
            pages = await asyncio.to_thread(run_scraping_pipeline, responses)
            save_checkpoint(job_id, "PAGES_SCRAPED", _dump(pages))
            await _transition(job_id, "PAGES_SCRAPED")
        else:
            log.info("job %s — PAGES_SCRAPED (cached)", job_id)
            pages = _load(load_checkpoint(job_id, "PAGES_SCRAPED"), "PAGES_SCRAPED")
        if start_idx < STAGE_ORDER.index("PRELIM_ANALYSES_COMPLETE"):
            log.info("job %s — PRELIM_ANALYSES_COMPLETE", job_id)
            analyses = await run_haiku_analysis(pages, query)
            save_checkpoint(job_id, "PRELIM_ANALYSES_COMPLETE", _dump(analyses))
            await _transition(job_id, "PRELIM_ANALYSES_COMPLETE")
        else:
            log.info("job %s — PRELIM_ANALYSES_COMPLETE (cached)", job_id)
            analyses = _load(load_checkpoint(job_id, "PRELIM_ANALYSES_COMPLETE"), "PRELIM_ANALYSES_COMPLETE")

        if start_idx < STAGE_ORDER.index("BLUEPRINT_READY"):
            log.info("job %s — BLUEPRINT_READY", job_id)
            blueprint = await run_consolidator(analyses, query, word_count)
            save_checkpoint(job_id, "BLUEPRINT_READY", _dump(blueprint))
            await _transition(job_id, "BLUEPRINT_READY")
        else:
            log.info("job %s — BLUEPRINT_READY (cached)", job_id)
            blueprint = _load(load_checkpoint(job_id, "BLUEPRINT_READY"), "BLUEPRINT_READY")

        if start_idx < STAGE_ORDER.index("ARTICLE_GENERATED"):
            log.info("job %s — ARTICLE_GENERATED", job_id)
            written = await run_writer(blueprint, word_count)
            save_checkpoint(job_id, "ARTICLE_GENERATED", _dump(written))
            await _transition(job_id, "ARTICLE_GENERATED")
        else:
            log.info("job %s — already ARTICLE_GENERATED", job_id)

    except Exception as exc:
        job_try = ctx.get("job_try", 1)
        log.exception("job %s failed on attempt %d/%d", job_id, job_try, MAX_TRIES)

        if job_try >= MAX_TRIES:
            # Exhausted all retries — mark permanently failed
            await _transition(job_id, "FAILED", error=str(exc))
            return  # don't raise — job is done, just failed
        delay = RETRY_DELAY[min(job_try - 1, len(RETRY_DELAY) - 1)]
        set_job_status(job_id, "RETRYING", error=str(exc))
        await push_stage(job_id, "RETRYING", error=f"attempt {job_try}/{MAX_TRIES}, retrying in {delay}s")
        raise Retry(defer=delay)


# Wrap with ARQ retry settings — timeout per attempt, not total
pipeline_job = arq_func(pipeline_task, max_tries=MAX_TRIES, timeout=3600)

class WorkerSettings:
    functions          = [pipeline_job]
    redis_settings     = RedisSettings.from_dsn(settings.redis_url)
    max_jobs           = 1
    retry_jobs         = True   # re-enqueue jobs that were mid-flight when worker died
    health_check_interval = 30  # detect dead workers faster (default 60s)
