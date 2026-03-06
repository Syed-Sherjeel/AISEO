import logging

from fastapi import FastAPI
from app.src.db import init_db


from arq import create_pool
from arq.connections import RedisSettings
from app.src.config import settings

from app.src.api.v1 import v1_enqueue_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Article Pipeline")

app.include_router(v1_enqueue_router)

@app.on_event("startup")
async def startup():
    init_db()
    app.state.redis = await create_pool(RedisSettings.from_dsn(settings.redis_url))  # ← app.state, not a global
    log.info("Redis pool ready, DB initialised")

@app.on_event("shutdown")
async def shutdown():
    await app.state.redis.aclose()

