# app/dependencies/rate_limiter.py

import time
from fastapi import Depends, HTTPException, Request, status
from redis.asyncio import Redis

from app.config import settings


async def get_redis(request: Request) -> Redis:
    """
    Expects app.state.redis to be set at startup. Add this to main.py:

        from redis.asyncio import Redis

        @app.on_event("startup")
        async def startup():
            app.state.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

        @app.on_event("shutdown")
        async def shutdown():
            await app.state.redis.aclose()
    """
    return request.app.state.redis


async def upload_rate_limiter(
    request: Request,
    redis: Redis = Depends(get_redis),
) -> None:
    """
    Sliding-window rate limiter for upload endpoints, keyed by client IP.
    Limits are read from settings (configured via .env):

        UPLOAD_RATE_LIMIT=10
        UPLOAD_RATE_WINDOW_SECONDS=60

    Apply to any upload route:

        @router.post("/upload")
        async def upload(..., _: None = Depends(upload_rate_limiter)):
            ...
    """
    ip = request.client.host
    now = int(time.time())
    window = settings.UPLOAD_RATE_WINDOW_SECONDS
    limit = settings.UPLOAD_RATE_LIMIT

    # Redis key is unique per IP per time window bucket
    window_bucket = now // window
    key = f"rate_limit:upload:{ip}:{window_bucket}"

    count = await redis.incr(key)

    # Set TTL on first request so the key auto-expires after the window
    if count == 1:
        await redis.expire(key, window)

    if count > limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=(
                f"Upload limit reached: {limit} uploads "
                f"per {window} seconds. Please try again later."
            ),
        )