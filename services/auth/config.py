from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    # access_token is exchange-only — short TTL by design
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 5
    # api_token is the long-lived token used for all API calls
    API_TOKEN_EXPIRE_SECONDS: int = 3600  # 60 minutes
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:3000",
        "http://localhost:8001",
        "http://localhost:8002",
        "http://localhost:8003",
        "http://localhost:8004",
    ]

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
