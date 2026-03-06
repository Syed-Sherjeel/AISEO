
import asyncio
import logging
from app.src.db import (
    save_checkpoint, load_checkpoint,
    set_job_status, last_completed_stage, get_job,
    STAGE_ORDER,
)
from app.src.services.serper import get_serper_responses
from app.src.services.scrapper import run_scraping_pipeline
from app.src.services.prelim import run_haiku_analysis
from app.src.services.consolidator import run_consolidator
from app.src.services.writer import run_writer

log = logging.getLogger(__name__)


def _dump(obj) -> dict:
    """
    Recursively serialize pydantic models (v1 or v2) or plain dicts/lists.
    Handles pydantic-of-pydantic-of-pydantic structures automatically.
    """
    if hasattr(obj, "model_dump"):          
        return obj.model_dump()
    if hasattr(obj, "dict"):              
        return obj.dict()
    if isinstance(obj, list):
        return [_dump(i) for i in obj]
    if isinstance(obj, dict):
        return {k: _dump(v) for k, v in obj.items()}
    return obj                             


def run_pipeline(job_id: str) -> None:
    """
    Execute all five stages in order, skipping any that already have a
    saved checkpoint.  Designed to be called from a background thread.
    """
    job = get_job(job_id)
    if not job:
        log.error("job %s not found", job_id)
        return

    query      = job["query"]
    word_count = job["word_count"]
    resume_from = last_completed_stage(job_id)
    start_idx   = STAGE_ORDER.index(resume_from)  # re-run from NEXT stage

    log.info("job %s — resuming after %s", job_id, resume_from)
    set_job_status(job_id, resume_from if resume_from != "PENDING" else "PENDING")

    try:
        
        if start_idx < STAGE_ORDER.index("SERP_FETCHED"):
            log.info("job %s — stage SERP_FETCHED", job_id)
            responses = get_serper_responses(query)
            save_checkpoint(job_id, "SERP_FETCHED", _dump(responses))
            set_job_status(job_id, "SERP_FETCHED")
        else:
            log.info("job %s — skipping SERP_FETCHED (cached)", job_id)
            responses = load_checkpoint(job_id, "SERP_FETCHED")

        if start_idx < STAGE_ORDER.index("PAGES_SCRAPED"):
            log.info("job %s — stage PAGES_SCRAPED", job_id)
            pages = run_scraping_pipeline(responses)
            save_checkpoint(job_id, "PAGES_SCRAPED", _dump(pages))
            set_job_status(job_id, "PAGES_SCRAPED")
        else:
            log.info("job %s — skipping PAGES_SCRAPED (cached)", job_id)
            pages = load_checkpoint(job_id, "PAGES_SCRAPED")

        if start_idx < STAGE_ORDER.index("ANALYSES_COMPLETE"):
            log.info("job %s — stage ANALYSES_COMPLETE", job_id)
            analyses = asyncio.run(run_haiku_analysis(pages, query))
            save_checkpoint(job_id, "ANALYSES_COMPLETE", _dump(analyses))
            set_job_status(job_id, "ANALYSES_COMPLETE")
        else:
            log.info("job %s — skipping ANALYSES_COMPLETE (cached)", job_id)
            analyses = load_checkpoint(job_id, "ANALYSES_COMPLETE")

        if start_idx < STAGE_ORDER.index("BLUEPRINT_READY"):
            log.info("job %s — stage BLUEPRINT_READY", job_id)
            blueprint = asyncio.run(run_consolidator(analyses, query, word_count))
            save_checkpoint(job_id, "BLUEPRINT_READY", _dump(blueprint))
            set_job_status(job_id, "BLUEPRINT_READY")
        else:
            log.info("job %s — skipping BLUEPRINT_READY (cached)", job_id)
            blueprint = load_checkpoint(job_id, "BLUEPRINT_READY")

        if start_idx < STAGE_ORDER.index("ARTICLE_GENERATED"):
            log.info("job %s — stage ARTICLE_GENERATED", job_id)
            written = asyncio.run(run_writer(blueprint, word_count))
            save_checkpoint(job_id, "ARTICLE_GENERATED", _dump(written))
            set_job_status(job_id, "ARTICLE_GENERATED")
        else:
            log.info("job %s — already ARTICLE_GENERATED", job_id)

    except Exception as exc:
        log.exception("job %s failed", job_id)
        set_job_status(job_id, "FAILED", error=str(exc))
