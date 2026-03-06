from fastapi import Request
from arq import ArqRedis

def get_redis(request: Request) -> ArqRedis:
    return request.app.state.redis