from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    # Explicitly list every origin that must be allowed to call this service.
    # Includes all service Swagger UI ports so cross-service docs login works.
    CORS_ORIGINS: List[str] = [
        "http://localhost",        # Nginx / frontend via port 80
        "http://localhost:3000",   # React dev server
        "http://localhost:8001",   # Auth service docs
        "http://localhost:8002",   # Prompt service docs
        "http://localhost:8003",   # Social service docs
        "http://localhost:8004",   # AI service docs
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
