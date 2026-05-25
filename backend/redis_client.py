import redis.asyncio as redis
from app.config import settings

# Dependency to inject Redis into your routers
async def get_redis():
    # decode_responses=True ensures we get strings back instead of bytes
    client = redis.from_url(settings.REDIS_URL, decode_responses=True)
    try:
        yield client
    finally:
        await client.aclose()