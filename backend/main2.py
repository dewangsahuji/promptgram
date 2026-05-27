from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth, prompts, social, image, user, collection
from app.database import engine, Base
import os

IS_PROXIED = os.getenv("BEHIND_PROXY", "false").lower() == "true"

app = FastAPI(
    title="Prompt Platform API",
    version="1.0",
    # root_path="/api" if IS_PROXIED else "",  # only set when behind Nginx etc.
)

# Create tables if not using Alembic
Base.metadata.create_all(bind=engine)  # remove this if using Alembic

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