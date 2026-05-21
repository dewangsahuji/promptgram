from fastapi import FastAPI

from app.database import Base
from app.database import engine

from app.models.user import User

Base.metadata.create_all(bind=engine)

app = FastAPI()


@app.get("/")
async def root():
    return {"message": "API running"}