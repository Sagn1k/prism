from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql+asyncpg://prism:prism@localhost:5432/prism"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET: str = "change-me-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRY_DAYS: int = 7

    # Claude AI
    CLAUDE_API_KEY: str = ""
    CLAUDE_MODEL: str = "claude-sonnet-4-20250514"

    # AWS / S3
    AWS_ACCESS_KEY: str = ""
    AWS_SECRET_KEY: str = ""
    S3_BUCKET: str = ""
    S3_REGION: str = "ap-south-1"

    # OTP
    OTP_EXPIRY_SECONDS: int = 300

    # WhatsApp
    WHATSAPP_API_URL: str = ""
    WHATSAPP_API_TOKEN: str = ""

    # App
    APP_URL: str = "http://localhost:3000"
    APP_ENV: str = "development"

    # Local file storage (dev alternative to S3)
    LOCAL_STORAGE_PATH: str = "./storage"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()


def get_settings() -> Settings:
    return settings
