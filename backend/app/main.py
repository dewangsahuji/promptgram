from fastapi import FastAPI

from app.database import Base
from app.database import engine

from app.models.user import User

from app.routers.auth import router as auth_router

Base.metadata.create_all(bind=engine)

app = FastAPI()

app.include_router(auth_router)


@app.get("/")
async def root():
    return {"message": "API running"}