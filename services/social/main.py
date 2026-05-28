from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from redis_client import close_redis
from routers import social, collections, users


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: close Redis connection pool
    await close_redis()


app = FastAPI(title="Social Service", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(social.router)
app.include_router(collections.router, prefix="/collections")
app.include_router(users.router, prefix="/users")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "social"}
