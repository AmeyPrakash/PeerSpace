<div align="center">

# PeerSpace

### Anonymous Campus Peer Mental Health, CBT Coach & Live Voice Platform

[![FastAPI](https://img.shields.io/badge/FastAPI-0.115+-009688.svg?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![Python](https://img.shields.io/badge/Python-3.11+-3776AB.svg?style=flat&logo=python&logoColor=white)](https://www.python.org)
[![Groq](https://img.shields.io/badge/Groq-Llama%203.3%20%2F%20GPT--OSS-F05032.svg?style=flat)](https://groq.com)
[![WebRTC](https://img.shields.io/badge/WebRTC-P2P%20Voice-333333.svg?style=flat&logo=webrtc&logoColor=white)](https://webrtc.org)
[![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

*A privacy-first, zero-PII student support platform combining empathetic AI CBT peer coaching, encrypted Student-to-Student live voice chat, and automatic real-time campus counselor escalation.*

</div>

---

## Highlights & Features

- **Empathetic AI CBT Peer Coach**:
  - Strictly operates as a peer counselor with Cognitive Behavioral Therapy techniques (identifies catastrophizing, all-or-nothing thinking, mind reading, and emotional reasoning).
  - Human classmate tone with natural college slang mirroring (`cooked`, `fr`, `ngl`, `tbh`, `lowkey`).
  - Zero robotic AI disclaimers or canned assistant language.

- **Strict Language & Script Adherence**:
  - Automatically matches and responds in the student's exact language and script (English, Hindi in Devanagari, conversational Hinglish in Latin script, Spanish, French, etc.).
  - Seamless code-switching and bilingual phrase mirroring without translating or defaulting to English.

- **Single-Purpose Coaching Guardrail**:
  - Strictly limited to emotional support, stress, and mental wellbeing.
  - Programmatic filters and prompt guardrails naturally deflect coding, homework, math, trivia, and jailbreak requests into emotional workload check-ins.

- **Encrypted Student-to-Student Live Voice Chat**:
  - Anonymous peer matchmaking radar powered by WebSocket signaling (`/ws/voice-room`).
  - True Peer-to-Peer WebRTC encrypted audio streaming.
  - Real-time Web Audio API speech activity visualizer and in-call emergency counselor trigger.

- **Campus Counselor Triage Portal**:
  - Authenticated on-call staff dashboard with secure passkey authentication.
  - Real-time acute crisis & self-harm risk queue with 1-click counselor dispatch.
  - Active anonymous student session monitor.

- **24/7 National Emergency Helplines**:
  - **Jeevan Aastha Helpline**: `1800 233 3330` (24/7 Toll-Free & Confidential)
  - **Aasra Crisis Support**: `09820466726` (24/7 Suicide Prevention)
  - **Tele-MANAS**: `14416` / `1800 891 4416` (National Mental Health Support)
  - **Kiran Mental Health**: `1800 599 0019` (Govt Multi-lingual Support)

- **Minimalist Editorial UI**:
  - Built with warm monochrome aesthetics (`#0C0E12`), editorial serif typography (`Newsreader`), geometric sans (`Geist`), and physical `<kbd>` keystrokes.
  - Zero emojis across the codebase and user interface (replaced with clean SVG icons).

---

## System Architecture

```text
PeerSpace/
├── agent/                         # Core AI & CBT ReAct Agent Package
│   ├── __init__.py                # Package exports (PeerSpaceAgent, tools, alerts)
│   ├── agent.py                   # ReAct Agent loop, session memory & guardrails
│   ├── prompts.py                 # Human peer persona, CBT distortion rules & safety
│   ├── react_chain.py             # Standalone ReAct pipeline runner
│   └── tools.py                   # CBT distortion identifier, 24/7 crisis safety & tools
│
├── backend/                       # Backend FastAPI API & WebSocket Signaling
│   ├── __init__.py                # Application instance export
│   ├── app.py                     # FastAPI application factory & router mounting
│   ├── config.py                  # Environment & settings configuration
│   ├── middleware.py              # Security headers (CSP, nosniff, DENY)
│   ├── rate_limiter.py            # Sliding window request rate limiter
│   ├── session_manager.py         # Zero-PII anonymous session & pseudonym generator
│   ├── voice_manager.py           # WebRTC signaling & peer matchmaking manager
│   ├── models/                    # Pydantic schemas & data validation
│   │   ├── __init__.py
│   │   └── schemas.py             # Strongly typed API contracts
│   └── routes/                    # Modular API route controllers
│       ├── __init__.py
│       ├── auth_routes.py         # Student pseudonym & Counselor passkey auth
│       ├── chat_routes.py         # AI CBT Coach interactions & session reset
│       ├── admin_routes.py        # Counselor alerts feed & active session tracking
│       └── voice_routes.py        # WebRTC WebSocket signaling & in-call escalation
│
├── frontend/                      # Responsive Minimalist Single-Page UI
│   ├── index.html                 # Semantic HTML5 UI with inline SVG icons
│   ├── css/
│   │   └── style.css              # Editorial dark design system & micro-animations
│   └── js/
│       └── app.js                 # WebRTC client, audio visualizer, chat & admin portal
│
├── tests/                         # Comprehensive Automated Test Suites
│   ├── __init__.py
│   ├── test_agent.py              # Persona, language mirroring & off-topic deflection
│   ├── test_full_system.py        # End-to-end API, chat & counselor escalation tests
│   ├── test_security.py           # Security headers, input validation & rate limiting
│   └── test_voice_matchmaking.py  # WebRTC WebSocket signaling & peer matching tests
│
├── server.py                      # Production entrypoint
├── Dockerfile                     # Multi-stage production container build
├── docker-compose.yml             # Docker composition manifest
├── Procfile                       # PaaS deployment manifest (Render, Railway, Heroku)
├── requirements.txt               # Pinned production Python dependencies
├── .dockerignore                  # Docker build exclusion rules
├── .gitignore                     # Git secrets & cache ignore rules
└── .env.example                   # Environment configuration template
```

---

## Quickstart Guide

### 1. Clone the Repository
```bash
git clone https://github.com/your-username/peerspace.git
cd peerspace
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env` and add your Groq API key:
```bash
cp .env.example .env
```

Edit `.env`:
```env
# Required: Groq LLM API Key (https://console.groq.com/keys)
GROQ_API_KEY=gsk_your_groq_api_key_here

# Required: Campus Counselor Portal Passkey (set to a strong, unique value)
COUNSELOR_PASSKEY=your_secure_passkey_here

# Optional Configurations
HOST=0.0.0.0
PORT=8000
GROQ_MODEL=openai/gpt-oss-120b
```

### 3. Install Dependencies
```bash
pip install -r requirements.txt
```

### 4. Run the Application
```bash
python server.py
```
Open **`http://127.0.0.1:8000`** in your browser.

---

## Automated Test Verification

Run all automated test suites to verify integrity:

```bash
# 1. Full System & AI Escalation Test Suite (8 tests)
python tests/test_full_system.py

# 2. Student-to-Student WebRTC Voice Matchmaking Suite (4 tests)
python tests/test_voice_matchmaking.py

# 3. Security Audit & Rate Limiter Suite (5 tests)
python tests/test_security.py

# 4. Agent Persona, CBT Distortions & Language Adherence Suite (8 tests)
python tests/test_agent.py
```

---

## Production Deployment

### Docker Deployment
```bash
# Build the optimized multi-stage image
docker build -t peerspace .

# Run container with environment bindings
docker run -d -p 8000:8000 --env-file .env peerspace
```

### Docker Compose
```bash
docker-compose up -d --build
```

### Cloud PaaS (Render, Railway, Fly.io, AWS ECS)
1. Push this repository to your GitHub account.
2. Connect your repository to Render / Railway.
3. Set the environment variable `GROQ_API_KEY`.
4. The deployment will automatically utilize the included `Dockerfile` or `Procfile` (`web: python server.py`) and monitor health via `GET /api/health`.

---

## Security & Zero-PII Policy

- **No Student Accounts**: Students connect under dynamic randomly generated campus pseudonyms (e.g. `MindfulFalcon88`, `WarmPanda51`).
- **Ephemeral Session Memory**: In-memory LRU session cache with automatic expiration and zero persistent database PII storage.
- **Strict Headers**: Hardened with Content Security Policy (CSP), `X-Content-Type-Options: nosniff`, `X-Frame-Options: DENY`, and strict referrer policies.
- **Sliding-Window Rate Limiter**: IP and session-bound request throttling to prevent flooding and abuse.

---

## License

This project is licensed under the [MIT License](LICENSE).
