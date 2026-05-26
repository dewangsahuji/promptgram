from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth , prompts , social , image , user , collection
from app.database import engine
from app.database import Base
from contextlib import asynccontextmanager


app = FastAPI(
    title="Prompt Platform API",
    version="1.0",
    root_path="/api",
)

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield


# Setup CORS for your React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change this to your frontend URL in production
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
    return {"message": "Api is running"}