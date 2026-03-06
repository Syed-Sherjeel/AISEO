import logging

from fastapi import FastAPI
from app.src.db import init_db

from app.src.api.v1 import v1_enqueue_router

logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

app = FastAPI(title="Article Pipeline")

app.include_router(v1_enqueue_router)

@app.on_event("startup")
def startup():
    init_db()
    log.info("DB initialised at jobs.db")
