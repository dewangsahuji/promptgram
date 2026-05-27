from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routers import social, collections, users
from database import engine, Base

app = FastAPI(title="Social Service", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(social.router)
app.include_router(collections.router, prefix="/collections")
app.include_router(users.router, prefix="/users")


@app.get("/health")
async def health():
    return {"status": "healthy", "service": "social"}
