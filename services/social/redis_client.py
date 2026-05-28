from redis.asyncio import Redis, from_url
from config import settings

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = from_url(settings.REDIS_URL, encoding="utf-8", decode_responses=True)
    return _redis


async def close_redis():
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
