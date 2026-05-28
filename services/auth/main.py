from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from database import Base, engine
from routers import auth, prompt_auth, images_auth, social_auth


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create all tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    # Shutdown: dispose engine
    await engine.dispose()


app = FastAPI(
    title="Auth Service",
    version="1.0",
    description="Authentication and authorization microservice for Promptgram.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─── Core auth (login / signup / me / logout) ─────────────────────────────────
app.include_router(auth.router, prefix="/auth")

# ─── Authenticated prompt endpoints (proxied to prompt-service) ───────────────
app.include_router(prompt_auth.router, prefix="/prompts")

# ─── Authenticated image endpoints (proxied to prompt-service) ────────────────
app.include_router(images_auth.router, prefix="/images")

# ─── Authenticated social endpoints (proxied to social-service) ───────────────
app.include_router(social_auth.router)


@app.get("/health", tags=["health"])
async def health():
    return {"status": "healthy", "service": "auth"}
