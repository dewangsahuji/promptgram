#config.py
from pydantic_settings import BaseSettings ,SettingsConfigDict


class Settings(BaseSettings):

    ENVIRONMENT:str = "testing"

    # Database URLs
    REDIS_URL: str
    DATABASE_URL: str

    # AWS S3
    AWS_ACCESS_KEY_ID:str
    AWS_SECRET_ACCESS_KEY:str
    AWS_REGION:str
    S3_BUCKET_NAME:str
    S3_ENDPOINT_URL: str = ""

    # Auth
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Upload rate limiting (applied per IP via upload_rate_limiter dependency)
    UPLOAD_RATE_LIMIT: int = 10              # max uploads per window
    UPLOAD_RATE_WINDOW_SECONDS: int = 60    # window size in seconds

    # Qdrant Settings (from your blueprint)
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333

    # Pydantic v2 recommended way to load .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore" # This tells Pydantic to ignore any other random env vars
    )

settings = Settings()

