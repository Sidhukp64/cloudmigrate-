from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import field_validator
import json


class Settings(BaseSettings):
    # App
    APP_NAME: str = "CloudMigrate"
    DEBUG: bool = False
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Database
    DATABASE_URL: str

    # Redis / Celery
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/0"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/1"

    # AWS S3
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "us-east-1"
    AWS_S3_BUCKET: str = "cloudmigrate-data"
    AWS_ENDPOINT_URL: Optional[str] = None

    # SFTP
    SFTP_HOST: str = "localhost"
    SFTP_PORT: int = 22
    SFTP_USER: str = ""
    SFTP_PASSWORD: str = ""
    SFTP_PRIVATE_KEY_PATH: Optional[str] = None

    # Webhooks
    WEBHOOK_SECRET: str = "default-secret"
    WEBHOOK_TIMEOUT_SECONDS: int = 10
    WEBHOOK_MAX_RETRIES: int = 3

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000"]

    # Rate limiting
    RATE_LIMIT_PER_MINUTE: int = 60

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            try:
                return json.loads(v)
            except Exception:
                return [v]
        return v

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
