<div align="center">

# PeerSpace

### Anonymous Campus Peer Support, CBT Companion & Encrypted Voice Network

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%20%2F%20GPT--OSS-F05032.svg?style=flat)](https://groq.com)
[![WebRTC](https://img.shields.io/badge/WebRTC-P2P%20Voice-333333.svg?style=flat&logo=webrtc&logoColor=white)](https://webrtc.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?style=flat&logo=docker&logoColor=white)](Dockerfile)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

*A zero-footprint, privacy-first platform where college students work through burnout, talk things out over encrypted peer audio, or get confidential human support when things get heavy.*

</div>

---

## Why PeerSpace?

Most campus mental health systems have good intentions but high barriers: login portals, two-week waiting lists, intake forms, and the lingering dread that asking for help goes on an academic record. When midterms hit at 2:00 AM, students don't need a bureaucratic intake—they need a safe outlet.

PeerSpace strips away identity entirely. There are no accounts, no tracking cookies, and no database logs tying anyone's thoughts to an email or student ID. Instead, students get three clean paths to relief:

1. **An AI CBT Companion** that sounds like an empathetic classmate, untangling cognitive distortions (catastrophizing, all-or-nothing spirals) without sounding like a robotic lecture.
2. **Encrypted 1-on-1 Voice & Text Chat** that pairs two anonymous students on the same campus radar for private conversations that vanish when the tab closes.
3. **A Discreet Counselor Triage Bridge** where certified campus staff can monitor anonymized risk flags in real time and quietly intervene in a session if a student is in acute danger.

---

## Key Capabilities

### 1. Empathetic CBT Peer Coach
- **Speaks the Language**: Mirroring conversational campus cadence (`cooked`, `fr`, `lowkey`, `burnout`, `spiraling`) so students feel heard rather than analyzed.
- **Multilingual & Hinglish**: Naturally switches between English, conversational Hinglish (Latin script), and Hindi (Devanagari script) without clunky machine translation.
- **Cognitive Distortion Spotting**: Pinpoints cognitive traps—all-or-nothing thinking, emotional reasoning, fortune telling, and overgeneralization—and counters them with grounding tools (box breathing, 5-4-3-2-1 sensory exercises).
- **Hardened Single-Purpose Guardrails**: Automatically deflects coding homework, math questions, trivia, and jailbreak prompts back into emotional check-ins.

### 2. Encrypted Anonymous Peer Voice Calls
- **Matchmaking Radar**: Instant student-to-student pairing over low-latency WebSockets (`/ws/voice-room`).
- **End-to-End P2P Audio**: Browser-to-browser WebRTC encrypted media pipes. Audio streams directly between students—the server only relays the initial handshake.
- **Live Waveform Visualizer**: Web Audio API frequency analysis for real-time speech visualizers without storing audio packets.
- **In-Call Escalation**: A single tap lets a peer request immediate campus counselor intervention if their partner is showing signs of crisis.

### 3. Real-Time Counselor Portal & Live Intervention
- **Triage Dashboard**: Campus counselors log in with a bcrypt-hashed passkey to view active sessions and pending crisis escalations.
- **Discreet Live Takeover**: Counselors can join a session directly. A clean banner lets the student know a human counselor is present, silencing the AI coach and routing replies directly to the professional.
- **Guaranteed Delivery & Deduplication**: Employs a dual-transport system (persistent WebSocket with automatic HTTP fallback) coupled with a 3-layer sliding-window deduplicator to prevent dropped or duplicate messages.

### 4. Zero-Footprint Security
- **No PII Ever Stored**: Pseudonyms are randomly generated (`QuietComet99`, `MindfulFalcon88`) and kept in ephemeral server memory.
- **Strict Headers**: Hardened with strict Content Security Policy (CSP), `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, and dynamic HTTPS Strict Transport Security (HSTS).
- **Brute-Force Lockout**: Rate-limiting with exponential backoff on authentication and sensitive endpoints.

---

## System Architecture

```text
  [ Student Browser ]                [ Campus Peer ]              [ Counselor Portal ]
    (Phone / Laptop)                 (Phone / Laptop)               (Staff Dashboard)
           │                                │                               │
           │  WebSocket / HTTP              │  WebRTC Audio                 │  WebSocket / HTTP
           ▼                                ▼                               ▼
┌────────────────────────────────────────────────────────────────────────────────────────┐
│                                   FASTAPI CORE ENGINE                                  │
│                                                                                        │
│  ┌───────────────────────────────┐                  ┌────────────────────────────────┐ │
│  │      Agentic CBT Brain        │                  │     Signaling & Sockets        │ │
│  │  • ReAct Decision Loop        │                  │  • /ws/voice-room (Matchmaking)│ │
│  │  • Distortion Detector        │                  │  • /ws/student    (Student WS) │ │
│  │  • Groq LLaMA-3.3 / GPT-OSS   │                  │  • /ws/counselor  (Counselor WS│ │
│  │  • Multilingual Grounding     │                  │  • 3-Tier Deduplication Cache  │ │
│  └───────────────────────────────┘                  └────────────────────────────────┘ │
│                                                                                        │
│  ┌───────────────────────────────┐                  ┌────────────────────────────────┐ │
│  │     Session & Security        │                  │     Crisis Safety Pipeline     │ │
│  │  • Ephemeral Memory Manager   │                  │  • Real-Time Alert Dispatcher  │ │
│  │  • Bcrypt Passkey Hashing     │                  │  • 1-Click Counselor Takeover  │ │
│  │  • Sliding Rate Limiter       │                  │  • 24/7 Helpline Integration   │ │
│  └───────────────────────────────┘                  └────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────────────────────┘
```

---

## Directory Structure

```text
PeerSpace/
├── agent/                         # Core AI & CBT ReAct Agent Package
│   ├── __init__.py                # Package exports
│   ├── agent.py                   # ReAct Agent loop, session memory & guardrails
│   ├── prompts.py                 # Peer persona, CBT distortion rules & safety prompts
│   ├── react_chain.py             # Standalone ReAct pipeline runner
│   └── tools.py                   # Distortion analyzers, grounding tools & crisis alerts
│
├── backend/                       # Backend FastAPI Services & Signaling
│   ├── __init__.py
│   ├── app.py                     # App factory, middleware & route mounting
│   ├── config.py                  # Environment settings & cross-platform path resolution
│   ├── middleware.py              # Security headers (CSP, nosniff, DENY, conditional HSTS)
│   ├── rate_limiter.py            # Sliding window request rate limiter & brute-force shield
│   ├── database.py                # Optional PostgreSQL engine & session factory
│   ├── session_manager.py         # Ephemeral zero-PII session & pseudonym generator
│   ├── voice_manager.py           # WebRTC signaling & peer matchmaking manager
│   ├── counselor_ws_manager.py    # Persistent WebSocket manager with duplicate suppression
│   ├── models/                    # Pydantic schemas & database models
│   │   ├── models.py              # Counselor applications & verification schemas
│   │   └── schemas.py             # Strongly typed API contracts
│   └── routes/                    # Modular API route controllers
│       ├── admin_routes.py        # Counselor alerts feed & active session tracking
│       ├── auth_routes.py         # Student pseudonym & counselor passkey auth
│       ├── chat_routes.py         # AI CBT Coach interactions & HTTP fallback replies
│       ├── counselor_routes.py    # Counselor application submission & OTP verification
│       ├── counselor_ws_routes.py # Bidirectional counselor intervention WebSockets
│       └── voice_routes.py        # WebRTC signaling & in-call safety escalations
│
├── Frontend/                      # Minimalist Single-Page Application
│   ├── index.html                 # Semantic HTML5 editorial interface
│   ├── css/
│   │   └── style.css              # Warm monochrome design system & micro-animations
│   └── js/
│       └── app.js                 # WebRTC client, audio visualizer, chat & staff dashboard
│
├── tests/                         # Automated Test Suites (100% Pass Rate)
│   ├── test_agent.py              # Persona, language mirroring & off-topic deflection
│   ├── test_full_system.py        # End-to-end API, chat & counselor escalation tests
│   ├── test_security.py           # Security headers, input validation & rate limiting
│   └── test_voice_matchmaking.py  # WebRTC WebSocket signaling & peer matching tests
│
├── server.py                      # Production entrypoint (Uvicorn runner)
├── Dockerfile                     # Hardened multi-stage container build
├── docker-compose.yml             # Container composition (App + PostgreSQL)
├── Procfile                       # PaaS deployment manifest (Render, Railway, Heroku)
├── requirements.txt               # Pinned Python dependencies
├── .env.example                   # Template environment configuration
├── .dockerignore                  # Docker build exclusion rules
└── .gitignore                     # Git secrets & cache ignore rules
```

---

## Quickstart

### 1. Prerequisites
- **Python 3.11+**
- A free **[Groq Cloud API Key](https://console.groq.com/keys)** (used for the fast-inference CBT companion)

### 2. Setup
```bash
# Clone the repository
git clone https://github.com/your-username/peerspace.git
cd peerspace

# Create and activate a virtual environment
python -m venv .venv
# On Windows:
.\.venv\Scripts\activate
# On macOS / Linux:
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Credentials
Copy the example environment file:
```bash
cp .env.example .env
```

Open `.env` and fill in your keys:
```env
# Required: Groq LLM API Key
GROQ_API_KEY=gsk_your_groq_api_key_here

# Required: Campus Counselor Staff Passkey
COUNSELOR_PASSKEY=your_secure_passkey_here

# Optional: Host & Port (defaults to 0.0.0.0:8000)
HOST=0.0.0.0
PORT=8000
```

### 4. Run Locally
```bash
python server.py
```
Open **`http://localhost:8000`** in your browser.

### 5. Testing Across Devices (Phones / Laptops on Local Wi-Fi)
Because PeerSpace binds to `0.0.0.0`, any device on the same local network can access it directly:
1. Find your machine's local IP address (`ipconfig` on Windows or `ifconfig` on Unix, e.g., `192.168.1.110`).
2. Open **`http://192.168.1.110:8000`** on your phone or a secondary device.
3. Open a second tab on your computer as a counselor at **`http://localhost:8000`**, enter your passkey, and experience the live intervention flow in real time.

---

## Automated Verification

PeerSpace ships with four self-contained test suites covering the entire system:

```bash
# 1. Security Headers, Input Sanitization & Flood Protection
python tests/test_security.py

# 2. WebRTC Signaling & Voice Matchmaking
python tests/test_voice_matchmaking.py

# 3. Full System, AI Escalation & Counselor Portal
python tests/test_full_system.py

# 4. Agent Persona, Distortion Spotting & Multilingual Mirroring
python tests/test_agent.py
```

---

## Production Deployment

### Option A: Docker (Recommended for VPS / Cloud Servers)
The included `Dockerfile` uses a multi-stage Python 3.11 build that runs under a non-privileged `peerspace` system user:

```bash
# Build the Docker image
docker build -t peerspace .

# Run the container (binds to port 8000 by default)
docker run -d -p 8000:8000 --env-file .env peerspace
```

Or spin up the full stack (App + PostgreSQL for counselor applications) via Docker Compose:
```bash
docker compose up -d --build
```

### Option B: Cloud PaaS (Render / Railway / Fly.io)
1. Push this repository to your GitHub account.
2. In **Render** or **Railway**, create a new **Web Service** from your repository.
3. Supply the environment variables:
   - `GROQ_API_KEY`
   - `COUNSELOR_PASSKEY`
4. The service will automatically pick up the `Procfile` or `Dockerfile`. PeerSpace supports dynamic `$PORT` assignment out of the box.

> **Note on Scaling**: Because student WebSockets and voice matchmaking queues are managed in fast in-memory registries, deploy with **`--workers 1`** or a single container instance to keep state unified without needing external Redis synchronization.

---

## Institutional Helplines & Safety

PeerSpace includes immediate access to 24/7 national emergency hotlines directly from the navigation bar:

- **Jeevan Aastha Helpline**: `1800 233 3330` (Toll-Free, 24/7)
- **Aasra Crisis Support**: `09820466726` (24/7 Suicide Prevention)
- **Tele-MANAS**: `14416` / `1800 891 4416` (National Mental Health Line)
- **Kiran Mental Health**: `1800 599 0019` (Govt Multilingual Support)

---

## License

Distributed under the [MIT License](LICENSE). Built for campuses, mental health advocates, and student communities everywhere.
