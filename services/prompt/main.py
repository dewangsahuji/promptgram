from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import engine, Base
from routers import prompts, images
from s3_client import ensure_bucket_exists


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Create DB tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    # Ensure S3/MinIO bucket exists
    await ensure_bucket_exists()
    yield


app = FastAPI(title="Prompt Service", version="1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prompts.router, prefix="/prompts")
app.include_router(images.router, prefix="/images")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "prompt"}
