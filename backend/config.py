"""
PeerSpace Backend Configuration
Loads environment variables and application settings.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

# Base paths
ROOT_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = ROOT_DIR / "frontend"
if not FRONTEND_DIR.exists():
    FRONTEND_DIR = ROOT_DIR / "Frontend"

# Load environment
env_path = ROOT_DIR / ".env"
load_dotenv(dotenv_path=env_path)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))

# SECURITY: COUNSELOR_PASSKEY must be set via environment variable
# DO NOT use a default passkey - it's a critical security vulnerability
_COUNSELOR_PASSKEY_PLAIN = os.getenv("COUNSELOR_PASSKEY")
if not _COUNSELOR_PASSKEY_PLAIN:
    raise ValueError(
        "CRITICAL: COUNSELOR_PASSKEY environment variable is not set. "
        "Please set a strong, unique passkey in your .env file or environment. "
        "Example: COUNSELOR_PASSKEY=your_strong_secure_passkey_here"
    )

# Hash the passkey on startup for secure verification
from backend.security import hash_passkey
COUNSELOR_PASSKEY_HASH = hash_passkey(_COUNSELOR_PASSKEY_PLAIN)

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
if not GROQ_API_KEY:
    raise ValueError(
        "CRITICAL: GROQ_API_KEY environment variable is not set. "
        "Please set your Groq API key in your .env file or environment."
    )

GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-120b")

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql+asyncpg://postgres:postgres@localhost:5432/peerspace")
