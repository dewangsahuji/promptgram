from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth , prompts , social , image , user , collection
from app.database import engine
from app.database import Base

app = FastAPI(title="Prompt Platform API", version="1.0" , root_path="/api")


@app.on_event("startup")
async def on_startup():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

# Setup CORS for your React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Change this to your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,    prefix="/api/auth")
app.include_router(prompts.router, prefix="/api/prompts")
app.include_router(social.router,  prefix="/api")
app.include_router(image.router,  prefix="/api/images")
app.include_router(user.router,   prefix="/api/users")
app.include_router(collection.router, prefix="/api/collections") 


@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def start():
    return {"message": "Api is running"}