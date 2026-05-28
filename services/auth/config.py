from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Downstream service URLs for proxy routing
    PROMPT_SERVICE_URL: str = "http://prompt-service:8002"
    SOCIAL_SERVICE_URL: str = "http://social-service:8003"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()

