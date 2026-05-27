import asyncio
from functools import partial

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from redis.asyncio import Redis
from app.routers import auth, prompts, social, image, user, collection
from app.database import engine, Base
from app.config import settings

from alembic.config import Config
from alembic import command

app = FastAPI(
    title="Prompt Platform API",
    version="1.0",
    root_path="/api"
)

@app.on_event("startup")
async def startup():
    # ── Run DB migrations ─────────────────────────────────
    alembic_cfg = Config("/app/alembic.ini")
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, partial(command.upgrade, alembic_cfg, "head"))

    # ── Connect Redis (used by rate limiter) ──────────────
    app.state.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)

@app.on_event("shutdown")
async def shutdown():
    await app.state.redis.aclose()

print("🚀 Go to http://localhost/api/docs to access the API documentation")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/auth")
app.include_router(prompts.router, prefix="/prompts")
app.include_router(social.router)
app.include_router(image.router, prefix="/images")
app.include_router(user.router, prefix="/users")
app.include_router(collection.router, prefix="/collections")

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def start():
    return {"message": "API is running"}