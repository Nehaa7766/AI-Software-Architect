"""Typed application settings loaded from environment variables.

Uses pydantic-settings so every secret/config value is validated and typed.
Import the singleton ``settings`` everywhere instead of reading os.environ.
"""
from functools import lru_cache
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", case_sensitive=False, extra="ignore"
    )

    # App
    ENVIRONMENT: Literal["development", "staging", "production", "test"] = "development"
    PORT: int = 8000
    CLIENT_ORIGIN: str = "http://localhost:3000"
    API_PREFIX: str = "/api"

    # Database
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_architect"

    # JWT / tokens
    ACCESS_TOKEN_SECRET: str = "change-me-access-secret"
    REFRESH_TOKEN_SECRET: str = "change-me-refresh-secret"
    ACCESS_TOKEN_TTL_MINUTES: int = 15
    REFRESH_TOKEN_TTL_DAYS: int = 7
    RESET_TOKEN_TTL_MINUTES: int = 30
    VERIFY_TOKEN_TTL_HOURS: int = 24
    JWT_ALGORITHM: str = "HS256"

    # Cookies
    COOKIE_SECURE: bool = False
    COOKIE_DOMAIN: str | None = None
    COOKIE_SAMESITE: Literal["lax", "strict", "none"] = "lax"
    REFRESH_COOKIE_NAME: str = "refresh_token"
    CSRF_COOKIE_NAME: str = "csrf_token"

    # Google OAuth
    GOOGLE_CLIENT_ID: str = ""

    # Mail
    MAIL_USERNAME: str = ""
    MAIL_PASSWORD: str = ""
    MAIL_FROM: str = "no-reply@example.com"
    MAIL_FROM_NAME: str = "AI Software Architect"
    MAIL_SERVER: str = "localhost"
    MAIL_PORT: int = 587
    MAIL_STARTTLS: bool = True
    MAIL_SSL_TLS: bool = False
    MAIL_SUPPRESS_SEND: bool = True

    # Uploads
    UPLOAD_DIR: str = "./uploads"
    MAX_AVATAR_BYTES: int = 2 * 1024 * 1024

    # Project import (Phase 1)
    WORKSPACE_DIR: str = "./workspace"
    # Temp dir for incoming archives before they are validated + extracted.
    PROJECT_TMP_DIR: str = "./workspace/.tmp"
    MAX_PROJECT_BYTES: int = 100 * 1024 * 1024  # max uploaded zip size
    MAX_PROJECT_UNCOMPRESSED_BYTES: int = 500 * 1024 * 1024  # zip-bomb guard
    MAX_PROJECT_FILES: int = 20_000  # max entries in an archive
    GITHUB_API_BASE: str = "https://api.github.com"
    GITHUB_CODELOAD_BASE: str = "https://codeload.github.com"
    GITHUB_DOWNLOAD_TIMEOUT_SECONDS: int = 60
    RATE_LIMIT_IMPORT: str = "10/minute"

    # Rate limiting
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "5/minute"
    RATE_LIMIT_FORGOT: str = "3/minute"

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def client_origins(self) -> list[str]:
        """Explicit allowed CORS origins (CLIENT_ORIGIN may be comma-separated)."""
        return [o.strip() for o in self.CLIENT_ORIGIN.split(",") if o.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
