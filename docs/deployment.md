# PeerSpace: Deployment & Vercel Serverless Architecture

This document explains how **PeerSpace** is deployed, with a focus on its **Vercel Serverless Python** architecture, compatibility considerations, resilient design patterns, and deployment verification.

---

## ☁️ Deployment Architecture Overview

PeerSpace is designed to run either as a persistent standalone server (via Uvicorn / Docker) or as a serverless application on **Vercel**:

```
                              [ Incoming Web Request ]
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    Vercel Serverless Edge Router     │
                      └──────────────────────────────────────┘
                                         │
                                         ▼
                      ┌──────────────────────────────────────┐
                      │    AWS Lambda Container (/var/task)  │
                      │    Python Runtime (@vercel/python)   │
                      │    Entrypoint: server.py (app)       │
                      └──────────────────────────────────────┘
                                    /        \
                                   /          \
                                  ▼            ▼
         ┌──────────────────────────────┐    ┌───────────────────────────┐
         │ Static UI: /Frontend         │    │ Neon Serverless Postgres  │
         │ HTML5, CSS3, Vanilla JS      │    │ (SSL, PgBouncer Pooler)   │
         └──────────────────────────────┘    └───────────────────────────┘
```

---

## 🔑 Key Deployment Requirements & Solutions

### 1. Serverless Entrypoint (`server.py`)
- **Module-Level App**: Vercel's Python runtime loader (`_vendor/vercel_runtime/vc_init.py`) expects the entrypoint module to expose an ASGI application instance named `app`.
- In [`server.py`](file:///c:/Users/Amey/Desktop/PeerSpace/server.py):
  ```python
  from backend.app import app
  ```
  This immediately exposes `app` at the module root so both local Uvicorn runs (`python server.py`) and Vercel serverless invocations load identically.

### 2. Resilient Configuration Fallback (`backend/config.py`)
- **The Problem**: In serverless runtimes, optional utility packages like `pydantic-settings` may fail to bundle or resolve during packaging if cached layers or minimal build environments are used, triggering `ModuleNotFoundError: No module named 'pydantic_settings'`.
- **The Solution**: [`backend/config.py`](file:///c:/Users/Amey/Desktop/PeerSpace/backend/config.py) implements a **dual-engine configuration loader**:
  - **Primary**: Attempts to load from `.env` using `pydantic-settings` with type validation and field validators.
  - **Fallback**: If `pydantic_settings` is absent or throws an `ImportError`, it catches the exception and falls back to a zero-dependency environment reader using Python's built-in `os.getenv` and `python-dotenv`.
  - **Result**: The backend **never** crashes on startup due to missing settings packages.

### 3. File System Case Sensitivity (`Frontend/`)
- **The Problem**: Windows file systems are case-insensitive, while Linux containers on Vercel (`/var/task`) are case-sensitive.
- **The Solution**: In [`backend/config.py`](file:///c:/Users/Amey/Desktop/PeerSpace/backend/config.py), the static assets path checks for the actual folder name in Git (`Frontend`) first, with a fallback to lowercase:
  ```python
  ROOT_DIR = Path(__file__).resolve().parent.parent
  FRONTEND_DIR = ROOT_DIR / "Frontend"
  if not FRONTEND_DIR.exists():
      FRONTEND_DIR = ROOT_DIR / "frontend"
  ```

### 4. Cross-Version Type Annotation Safety (`agent/tools.py`)
- **The Problem**: In Python versions prior to 3.14 without postponed annotations, type hints like `-> Tuple[bool, str]:` are evaluated at import time. If `Tuple` is missing from `from typing import ...`, the serverless worker crashes with `NameError: name 'Tuple' is not defined`.
- **The Solution**:
  - Added `from __future__ import annotations` at the top of [`agent/tools.py`](file:///c:/Users/Amey/Desktop/PeerSpace/agent/tools.py).
  - Explicitly imported `Tuple, Any` alongside `List, Dict, Optional`.
  - Scanned the entire codebase via Python AST visitors to ensure 100% annotation cleanliness.

### 5. Zero Runtime Disk Writes
- **The Problem**: Serverless environments provide a read-only root filesystem (`/var/task`). Any attempt to write local SQLite databases or file logs will fail.
- **The Solution**:
  - All persistent state (user accounts, counselor applications, appointments, community stories, wellness check-ins) lives exclusively in **Neon Serverless PostgreSQL**.
  - All active chat memory and AI reasoning buffers live ephemerally in RAM (`agent/memory.py`).
  - No SQLite files, logs, or cache files are written to the local disk at runtime.

---

## 📦 Requirements & Dependencies (`requirements.txt`)

To ensure smooth compilation and packaging on Vercel without pip solver deadlocks, dependencies are kept clean and unpinned in [`requirements.txt`](file:///c:/Users/Amey/Desktop/PeerSpace/requirements.txt):

```text
fastapi
uvicorn[standard]
pydantic
pydantic-settings
python-dotenv
httpx
jinja2
python-multipart
groq
bcrypt
sqlalchemy[asyncio]
psycopg[binary]
asyncpg
alembic
greenlet
websockets
wsproto
gunicorn
```

---

## ⚙️ Vercel Environment Variables Configuration

When setting up your project on the [Vercel Dashboard](https://vercel.com), configure the following environment variables under **Settings > Environment Variables**:

| Variable | Description | Example / Recommended Value |
| :--- | :--- | :--- |
| `DATABASE_URL` | Neon PostgreSQL pooled connection string | `postgresql://user:pass@ep-xyz-pooler.region.aws.neon.tech/peerspace?sslmode=require` |
| `GROQ_API_KEY` | Groq Cloud API key for AI Coach inference | `gsk_xxxxxxxxxxxxxxxxxxxxxxxx` |
| `GROQ_MODEL` | Groq LLM model name | `openai/gpt-oss-120b` or `llama-3.3-70b-versatile` |
| `COUNSELOR_PASSKEY` | Passkey for on-duty counselor portal | Secure random passphrase |
| `SECRET_KEY` | Secret key for JWT session tokens | 32+ character random hex string |
| `ENVIRONMENT` | Deployment environment | `production` |

---

## 🚀 Pre-Deployment Verification Checklist

Before pushing commits to trigger a Vercel deployment, run this quick local verification:

```powershell
# 1. Verify app imports cleanly in a fresh process
python -c "from server import app; print('App loaded successfully:', app.title)"

# 2. Test simulated serverless fallback (missing pydantic-settings)
python -c "import sys; sys.modules['pydantic_settings'] = None; from server import app; print('Fallback OK:', app.title)"

# 3. Run all automated test suites
python tests/test_agent_orchestration.py
python tests/test_agent_memory.py
python tests/test_security.py

# 4. Check git status
git status
```
