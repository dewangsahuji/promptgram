"""
services/auth/main.py
"""
from contextlib import asynccontextmanager

import redis.asyncio as aioredis
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from config import settings
from database import Base, engine, get_db
from redis_client import get_redis
from routers import auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # ── Startup ───────────────────────────────────────────────────────────────
    # Create tables if they don't exist.
    # NOTE: this is a convenience for local dev only. In production, run
    #       `alembic upgrade head` as part of your deployment pipeline instead.
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    yield

    # ── Shutdown ──────────────────────────────────────────────────────────────
    await engine.dispose()


app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    description="Authentication and authorization microservice for Promptgram.",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
# allow_origins="*" is incompatible with allow_credentials=True — browsers
# reject credentialed requests when the origin is a wildcard (CORS spec §3.2).
# Use an explicit allowlist instead. Set CORS_ORIGINS in your .env as a
# comma-separated list, e.g.: CORS_ORIGINS=http://localhost:3000,https://promptgram.com
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # list[str] from config
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(auth.router, prefix="/auth", tags=["auth"])


# ── Health ────────────────────────────────────────────────────────────────────
@app.get("/health", tags=["health"], summary="Liveness + dependency check")
async def health():
    """
    Returns 200 only when both PostgreSQL and Redis are reachable.
    The docker-compose healthcheck hits this endpoint, so a superficial
    'healthy' response would mask downstream failures.
    """
    checks: dict[str, str] = {}

    # PostgreSQL
    try:
        async for db in get_db():
            await db.execute(text("SELECT 1"))
        checks["postgres"] = "ok"
    except Exception as exc:
        checks["postgres"] = f"error: {exc}"

    # Redis
    try:
        async for redis in get_redis():
            await redis.ping()
        checks["redis"] = "ok"
    except Exception as exc:
        checks["redis"] = f"error: {exc}"

    all_ok = all(v == "ok" for v in checks.values())

    return {
        "status": "healthy" if all_ok else "degraded",
        "service": "auth",
        "checks": checks,
    }