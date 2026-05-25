from pydantic_settings import BaseSettings ,SettingsConfigDict


class Settings(BaseSettings):
    # Database URLs
    REDIS_URL: str
    DATABASE_URL: str

    # AWS S3
    AWS_ACCESS_KEY_ID:str
    AWS_SECRET_ACCESS_KEY:str
    AWS_REGION:str
    S3_BUCKET_NAME:str

    # Auth
    JWT_SECRET: str
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Qdrant Settings (from your blueprint)
    QDRANT_HOST: str = "qdrant"
    QDRANT_PORT: int = 6333

    # Pydantic v2 recommended way to load .env
    model_config = SettingsConfigDict(
        env_file=".env", 
        extra="ignore" # This tells Pydantic to ignore any other random env vars
    )

settings = Settings()