from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    APP_NAME: str = "s2s-service-smtp"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://user:password@localhost:5432/smtp_service"

    # Security
    SECRET_KEY_HASH: str = "your-secret-key"
    HASH_EXPIRATION_TIME: int = 300  # seconds

    # Rate limiting
    RATE_LIMIT: int = 10  # requests per minute
    RATE_LIMIT_WINDOW: int = 60  # seconds

    # Mail
    MAIL_HOST: str = "smtp.example.com"
    MAIL_PORT: int = 587
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "noreply@example.com"
    MAIL_FROM_NAME: str = "Notifications"
    MAIL_USE_TLS: bool = True

    # SMS - Gupshup
    SMS_API_URL: str = "https://enterprise.smsgupshup.com/GatewayAPI/rest"
    SMS_USERID: str = ""
    SMS_PASSWORD: str = ""
    SMS_METHOD: str = "SendMessage"
    SMS_VERSION: str = "1.1"
    SMS_SEND_TO_COUNTRY: str = "91"

    # AWS S3 (optional)
    AWS_ACCESS_KEY_ID: str = ""
    AWS_SECRET_ACCESS_KEY: str = ""
    AWS_REGION: str = "ap-south-1"
    AWS_BUCKET: str = ""

    # Redis (rate limiting)
    REDIS_URL: str = "redis://localhost:6379"

    # CORS
    ALLOWED_ORIGINS: List[str] = ["*"]

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
