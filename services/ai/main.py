from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from model_manager import load_models
from qdrant_client_helper import ensure_collection
from routers import embed, search, classify, moderate, pipeline


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load all ML models into app.state (takes 30–60s on first cold start)
    await load_models(app)
    # Ensure Qdrant collection exists
    await ensure_collection()
    yield


app = FastAPI(
    title="AI Service",
    version="1.0",
    description="CLIP embeddings · semantic search · auto-tagging · NSFW moderation",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(embed.router, prefix="/ai")
app.include_router(search.router, prefix="/ai")
app.include_router(classify.router, prefix="/ai")
app.include_router(moderate.router, prefix="/ai")
app.include_router(pipeline.router, prefix="/ai")


@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "service": "ai",
        "models_loaded": getattr(app.state, "models_loaded", False),
    }
