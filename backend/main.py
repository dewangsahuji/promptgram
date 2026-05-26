from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import auth , prompts , social , image
from app.database import engine
from app.database import Base

app = FastAPI(title="Prompt Platform API", version="1.0")


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



# Mount the auth router
app.include_router(auth.router, prefix="/auth")
app.include_router(prompts.router , prefix="/prompts")
app.include_router(social.router)
app.include_router(image.router)  # ✅ prefix="/images" is set inside the router



@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/")
async def start():
    return {"message": "Api is running"}