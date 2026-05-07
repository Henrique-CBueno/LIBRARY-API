from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Library Management API"
    APP_VERSION: str = "1.0.0"

    DATABASE_URL: str = "postgresql+asyncpg://admin:admin@postgres:5432/library"
    REDIS_URL: str = "redis://redis:6379"

    JWT_SECRET: str = "SUA_SECRET_KEY"
    JWT_EXPIRE_MINUTES: int = 60

    ENVIRONMENT: str = "development"

    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()