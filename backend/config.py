"""
PeerSpace Backend Configuration
Loads environment variables and application settings with resilient fallback.
"""

import os
from pathlib import Path
from dotenv import load_dotenv
from backend.security import hash_passkey

# Base paths - resolve absolute path relative to this file
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "Frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = ROOT_DIR / "frontend"

# Preload .env if available
env_file = ROOT_DIR / ".env"
if env_file.exists():
    load_dotenv(dotenv_path=env_file)
else:
    load_dotenv()

def normalize_database_url(url: str) -> str:
    """Normalize database URL for SQLAlchemy async engine with Psycopg 3 and Neon SSL."""
    url = (url or "").strip()
    # Adapt postgresql:// or postgres:// to postgresql+psycopg:// for SQLAlchemy with Psycopg 3
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql://") and not url.startswith("postgresql+"):
        url = url.replace("postgresql://", "postgresql+psycopg://", 1)
    elif url.startswith("postgresql+asyncpg://"):
        url = url.replace("postgresql+asyncpg://", "postgresql+psycopg://", 1)

    # Enforce SSL if connecting to Neon or cloud PostgreSQL
    if "neon.tech" in url and "sslmode" not in url:
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}sslmode=require"

    return url

try:
    from pydantic_settings import BaseSettings, SettingsConfigDict
    from pydantic import Field, field_validator

    class Settings(BaseSettings):
        """Application settings validated and loaded securely from .env via pydantic-settings."""
        model_config = SettingsConfigDict(
            env_file=str(ROOT_DIR / ".env"),
            env_file_encoding="utf-8",
            extra="ignore"
        )

        HOST: str = "0.0.0.0"
        PORT: int = 8000
        COUNSELOR_PASSKEY: str = Field(default="peerspace_passkey", description="Counselor access passkey")
        GROQ_API_KEY: str = Field(default="", description="Groq API key")
        GROQ_MODEL: str = "openai/gpt-oss-120b"
        DATABASE_URL: str = Field(
            default="postgresql+psycopg://postgres:postgres@localhost:5432/peerspace",
            description="PostgreSQL / Neon database connection URL"
        )

        @field_validator("DATABASE_URL", mode="after")
        @classmethod
        def _normalize_db_url(cls, v: str) -> str:
            return normalize_database_url(v)

    settings = Settings()

except (ImportError, ModuleNotFoundError, Exception):
    # Resilient fallback when pydantic-settings is not installed or fails in serverless runtime
    class FallbackSettings:
        def __init__(self):
            self.HOST: str = os.getenv("HOST", "0.0.0.0")
            try:
                self.PORT: int = int(os.getenv("PORT", "8000"))
            except ValueError:
                self.PORT = 8000
            self.COUNSELOR_PASSKEY: str = os.getenv("COUNSELOR_PASSKEY", "peerspace_passkey")
            self.GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
            self.GROQ_MODEL: str = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")
            raw_db_url = os.getenv(
                "DATABASE_URL",
                "postgresql+psycopg://postgres:postgres@localhost:5432/peerspace"
            )
            self.DATABASE_URL: str = normalize_database_url(raw_db_url)

    settings = FallbackSettings()

# Backwards-compatible exports for existing codebase imports
HOST = settings.HOST
PORT = settings.PORT
COUNSELOR_PASSKEY_HASH = hash_passkey(settings.COUNSELOR_PASSKEY)
GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_MODEL = settings.GROQ_MODEL
DATABASE_URL = settings.DATABASE_URL
