from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    AWS_ACCESS_KEY_ID: str
    AWS_SECRET_ACCESS_KEY: str
    AWS_REGION: str = "ap-south-1"
    S3_BUCKET_NAME: str
    # Optional: set this to use MinIO or another S3-compatible endpoint locally
    # e.g. S3_ENDPOINT_URL=http://minio:9000
    S3_ENDPOINT_URL: str | None = None
    # AI service URL for background pipeline calls
    AI_SERVICE_URL: str = "http://ai-service:8004"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
