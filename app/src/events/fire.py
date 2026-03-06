import logging
import asyncio
from ably import AblyRest

from app.src.utils.env import get_ably_api_key

log = logging.getLogger(__name__)

_ably: AblyRest | None = None

ably_api_key = get_ably_api_key()

def _client() -> AblyRest | None:
    global _ably
   
    if _ably is None:
        _ably = AblyRest(get_ably_api_key())
    return _ably

async def push_stage(job_id: str, status: str, error: str | None = None) -> None:
    client = _client()
    if client is None:
        log.debug("Ably not configured — skipping push for job %s", job_id)
        return
    try:
        channel = client.channels.get(f"job:{job_id}")
        await channel.publish(
            "stage_update",
            {"job_id": job_id, "status": status, "error": error},
        )
    except Exception:
        log.warning("Ably publish failed for job %s", job_id, exc_info=True)