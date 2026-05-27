from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/social_db"
    REDIS_URL: str = "redis://localhost:6379/2"
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    PROMPT_SERVICE_URL: str = "http://prompt-service:8002"
    AUTH_SERVICE_URL: str = "http://auth-service:8001"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
