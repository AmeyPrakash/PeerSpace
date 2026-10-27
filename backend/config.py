"""
PeerSpace Backend Configuration
Loads environment variables and application settings using pydantic-settings.
"""

from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator
from backend.security import hash_passkey

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = ROOT_DIR / "Frontend"

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
    def normalize_database_url(cls, v: str) -> str:
        url = v.strip()
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

# Instantiate settings singleton
settings = Settings()

# Backwards-compatible exports for existing codebase imports
HOST = settings.HOST
PORT = settings.PORT
COUNSELOR_PASSKEY_HASH = hash_passkey(settings.COUNSELOR_PASSKEY)
GROQ_API_KEY = settings.GROQ_API_KEY
GROQ_MODEL = settings.GROQ_MODEL
DATABASE_URL = settings.DATABASE_URL
