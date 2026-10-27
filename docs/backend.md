# PeerSpace: Backend & API Architecture Documentation

This document explains the **PeerSpace Backend** in simple, clear words—how the server is organized, how it talks to the database, how real-time WebSockets work, and how security is maintained.

---

## ⚙️ Backend Overview in Simple Words

The PeerSpace backend is built with **FastAPI** (Python). It acts as the central brain of the platform:
- It serves the web pages and static frontend files.
- It receives messages from students and coordinates with the **AI Coach**.
- It securely queries and stores data in **Neon Serverless PostgreSQL**.
- It manages real-time WebSockets so human counselors can monitor safety alerts live.
- It provides signaling for private student-to-student WebRTC voice calls.

---

## 🏛️ Project Structure & Key Modules

Here is how the backend files are structured:

```
backend/
├── app.py                     # Main FastAPI application and route registration
├── config.py                  # Pydantic-settings configuration (.env loader)
├── database.py                # Neon PostgreSQL connection, Psycopg 3, & session factory
├── chat_manager.py            # Peer-to-peer text chat matchmaking & relay
├── counselor_manager.py       # Counselor profiles & on-duty session management
├── counselor_ws_manager.py    # WebSocket hub for counselor live alerts & AI reasoning
├── middleware.py              # Security headers, CORS, and request logging
├── rate_limiter.py            # Abuse prevention & API rate limiting
├── security.py                # Password hashing (bcrypt) and JWT authentication
├── session_manager.py         # In-RAM student session tracker (zero-trace storage)
├── verification_manager_db.py # OTP code generation & verification in PostgreSQL
├── voice_manager.py           # WebRTC voice call matchmaking and signaling
├── models/                    # Database models and Pydantic request/response schemas
└── routes/                    # Modular API route controllers
    ├── admin_routes.py        # Counselor application review & moderation
    ├── auth_routes.py         # Login, registration, & OTP verification
    ├── chat_routes.py         # AI Coach chat, reasoning streaming, & intervention
    ├── counselor_routes.py    # Counselor portal data and alert triage
    └── voice_routes.py        # WebRTC call signaling endpoints
```

---

## 🔐 Secure Configuration (`backend/config.py`)

All configuration is managed with **`pydantic-settings`** and loaded from the project's root `.env` file:
- **No Hardcoded Secrets**: Credentials like database passwords, JWT secrets, and AWS keys are never written in the code.
- **Smart URL Normalization**: If the `DATABASE_URL` starts with `postgresql://` or `postgres://`, it is automatically converted to `postgresql+psycopg://` so SQLAlchemy uses the modern Psycopg 3 async driver.
- **Enforced SSL**: Enforces `sslmode=require` so all network traffic between our server and Neon PostgreSQL is encrypted.

---

## 🗄️ Database Connection & Pooling (`backend/database.py`)

PeerSpace connects to **Neon Serverless PostgreSQL** using:
1. **Psycopg 3 Async Driver**: Modern, fast asynchronous database driver for Python.
2. **NullPool with PgBouncer**: Since Neon handles connection pooling in the cloud with PgBouncer, the backend uses `NullPool` to let Neon manage connections efficiently without client-side stale connection issues.
3. **Reusable Session Dependency**: Route functions access the database cleanly using FastAPI's dependency injection:
   ```python
   @router.get("/example")
   async def example_route(db: AsyncSession = Depends(get_db)):
       # db is an active, managed session that closes automatically
       ...
   ```
4. **Windows Event Loop Support**: On Windows, Python's default event loop is automatically configured with `SelectorEventLoop` in [`server.py`](file:///c:/Users/Amey/Desktop/PeerSpace/server.py), ensuring 100% stability with Psycopg 3.

---

## 🩺 Safe Health-Check Endpoint (`/api/health`)

To allow monitoring without risking data leaks, the backend includes a zero-exposure health check:
- **Endpoint**: `GET /api/health`
- **What it does**: Runs a simple `SELECT 1` query against the database.
- **Success Response (HTTP 200)**:
  ```json
  {
    "status": "healthy",
    "database": "connected"
  }
  ```
- **Error Response (HTTP 503)**:
  ```json
  {
    "status": "unhealthy",
    "database": "disconnected"
  }
  ```
- **Security Guarantee**: Even if the database connection drops or credentials fail, internal error traces and connection strings are **never** returned to the browser or logged publicly. They are safely logged only on the server.

---

## 🚀 Key API Endpoints & Routes

### 1. AI Coach & Chat (`/api/chat`, `/api/reset`)
- **`POST /api/chat`**: Sends a message to the AI Coach. Runs the reasoning loop in a background thread, updates in-RAM context, and streams the reasoning to counselors.
- **`POST /api/reset`**: Immediately clears the student's in-RAM conversation context and restores a clean slate.
- **`POST /api/chat/escalate`**: Directly alerts campus counselors if the student requests human help.
- **`POST /api/chat/intervene`**: Allows a verified human counselor to step directly into the chat session, instantly pausing the AI and routing messages to the counselor.

### 2. Authentication & Verification (`/api/auth/*`)
- **`POST /api/auth/register`**: Registers a new student or counselor account.
- **`POST /api/auth/login`**: Authenticates credentials and returns a secure JWT token.
- **`POST /api/auth/send-otp`**: Generates and sends a temporary 6-digit OTP code.
- **`POST /api/auth/verify-otp`**: Validates the OTP code against the database.

### 3. Counselor & Admin Routes (`/api/counselor/*`, `/api/admin/*`)
- **`GET /api/counselor/alerts`**: Lists active student crisis alerts awaiting attention.
- **`POST /api/counselor/resolve-alert`**: Resolves an alert once human support is provided.
- **`GET /api/admin/applications`**: Lists pending counselor verification documents and credential applications.

---

## 📡 Real-Time WebSockets & Voice Signaling

PeerSpace features two distinct real-time WebSocket channels:

1. **Counselor Safety Channel (`/ws/counselor`)**:
   - Broadcasts real-time safety alerts whenever a student exhibits acute distress or requests human help.
   - Streams the AI Coach's internal reasoning so on-duty staff have context.
   - Allows counselors to send live intervention messages to active student rooms.

2. **WebRTC Voice & Peer Matchmaking (`/ws/voice`, `/ws/peer-chat`)**:
   - Matches students anonymously for 1-on-1 peer conversations.
   - Exchanges WebRTC SDP offers, answers, and ICE candidates for private, encrypted audio calls directly between peers.

---

## 🛡️ Security & Privacy Measures

1. **Password Protection**: Passwords are cryptographically hashed using **bcrypt** before hitting the database.
2. **Rate Limiting**: Custom sliding-window rate limiter prevents brute-force attacks and chat endpoint flooding.
3. **CORS & Security Headers**: Strict HTTP headers protect against XSS, clickjacking, and MIME-sniffing.
4. **Sanitized Logs**: Database passwords, connection strings, and student chat texts are excluded from console and file logs.

---

## 📁 Related Source Files

- **Application Root**: [`backend/app.py`](file:///c:/Users/Amey/Desktop/PeerSpace/backend/app.py)
- **Settings & Config**: [`backend/config.py`](file:///c:/Users/Amey/Desktop/PeerSpace/backend/config.py)
- **Database Engine**: [`backend/database.py`](file:///c:/Users/Amey/Desktop/PeerSpace/backend/database.py)
- **Chat Routes**: [`backend/routes/chat_routes.py`](file:///c:/Users/Amey/Desktop/PeerSpace/backend/routes/chat_routes.py)
- **Counselor Routes**: [`backend/routes/counselor_routes.py`](file:///c:/Users/Amey/Desktop/PeerSpace/backend/routes/counselor_routes.py)
- **Server Runner**: [`server.py`](file:///c:/Users/Amey/Desktop/PeerSpace/server.py)
