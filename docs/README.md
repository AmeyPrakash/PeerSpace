# PeerSpace: System Overview & Documentation Index

Welcome to the **PeerSpace** documentation! This guide explains what PeerSpace is, how it works, what we have recently built, and where to find detailed guides for every part of the system in simple, everyday words.

---

## 🌟 What is PeerSpace in Simple Words?

**PeerSpace** is a safe, anonymous campus mental health and peer support platform built for college students. 

College can be overwhelming—midterms, assignments, noisy roommates, and social anxiety can pile up fast. PeerSpace gives students a safe space to talk immediately without fear of judgment, stigma, or having their privacy compromised:

1. **A Kind AI Companion (AI Coach)**: Students can vent anytime. The AI listens, offers comforting perspective like an understanding friend, helps guide breathing exercises, and remembers what was shared earlier in the chat.
2. **Live Human Counselor Support**: If a student is going through a serious crisis or wants professional human support, on-duty campus counselors can view real-time safety alerts and step in directly via live chat or confidential voice calls.
3. **Campus Community & Professional Appointments**: Students can read peer stories, take confidential wellness assessments, and book appointments with verified counselors.
4. **Zero-Trace Privacy**: Conversations with the AI Coach live strictly in memory (RAM) while the session is active. They are never permanently saved to disk, ensuring complete privacy.

---

## 📂 Documentation Index

Detailed documentation for each component of the platform is organized into dedicated guides:

| Guide | Description |
| :--- | :--- |
| 🤖 [**AI Coach & Agent Docs**](agent.md) | How the AI works, the ReAct reasoning loop, in-memory context retention, human peer persona rules, Hinglish support, and crisis safety guardrails. |
| 🗄️ [**Database Docs & Storage Schema**](database.md) | Neon PostgreSQL database guide: **detailed plain-English breakdown of all 15 tables and exactly what they store**, Psycopg 3 setup, connection pooling, and Alembic migrations. |
| ⚙️ [**Backend & API Architecture**](backend.md) | FastAPI modular structure, `pydantic-settings` configuration, `/api/health` check with zero credential leakage, and WebSockets/WebRTC signaling. |
| 🎨 [**Frontend & Counselor Portal**](frontend.md) | User interfaces, student chat view, on-duty counselor portal, live AI reasoning stream, and privacy cleanups. |
| 🚀 [**Setup & How to Run**](setup_and_running.md) | Simple step-by-step instructions for running the server locally, managing environment variables, and testing connections. |
| ☁️ [**Deployment & Vercel Serverless**](deployment.md) | Serverless architecture guide, resilient configuration fallback pattern, cross-platform compatibility, and production readiness. |

---

## 🛠️ Summary of Recent Major Achievements

Here is what we have implemented, hardened, and polished:

1. **AI Coach Reasoning & Analysis**:
   - The AI now analyzes the user's situation and determines the most helpful action before generating its response.
   - Counselors on duty can observe this reasoning analysis live in their dashboard to understand how the student is doing.

2. **Ephemeral In-RAM Memory**:
   - Built a zero-footprint memory system. The AI remembers student stressors (like an upcoming exam or roommate tension) and grounding tools used earlier in the chat.
   - When the session ends, the memory disappears from RAM. Nothing is written to files.

3. **Human Peer Persona ("Kind Friend")**:
   - Replaced clinical therapist clichés (*"It sounds like you're feeling anxious"* or *"Would you like to explore those feelings?"*) with direct, warm, supportive language (*"It's okay—one mistake doesn't define who you are"*).
   - Kept responses short (1–3 sentences) and natural. Added support for authentic Hinglish code-switching without robotic script mixing.

4. **Counselor Portal Cleanliness & Real-Time Sync**:
   - Removed internal cognitive debug profiles (`🧠 Student Memory & Context Profile`) from the counselor window so counselors have a clean, focused view of the chat and live reasoning stream.
   - Fixed counselor state persistence on refresh so the "Counselor Active" banner never gets stuck.
   - Fixed WebRTC voice join button to directly connect counselor and student via live audio rather than defaulting to text chat.

5. **Neon PostgreSQL & Psycopg 3 Migration**:
   - Connected the FastAPI backend directly to **Neon Serverless PostgreSQL** (PostgreSQL 18.6).
   - Configured `pydantic-settings` to securely load and validate `DATABASE_URL` from `.env`.
   - Switched to the modern **Psycopg 3** driver with native SSL enforcement and PgBouncer connection pooling.
   - Enhanced `/api/health` to verify database health (`SELECT 1`) with zero credential or internal error leakage.

6. **AI Agent Orchestration Engine**:
   - Implemented full ReAct tool-calling loop with strict budget enforcement (`MAX_ITERATIONS = 4`, `MAX_TOOL_BUDGET = 3`).
   - Added pre-generation crisis safety fast-path that intercepts acute crisis keywords in English and Hinglish and triggers critical counselor alerts with 24/7 helpline contacts without waiting for LLM generation.
   - Added post-generation anti-fabrication filter preventing the model from claiming false actions.
   - Built a zero-tool fast path for natural, direct conversational turns.

7. **Vercel Serverless Deployment Compatibility & Resilient Config**:
   - Built a resilient fallback configuration loader in [`backend/config.py`](file:///c:/Users/Amey/Desktop/PeerSpace/backend/config.py) that catches import errors and uses standard environment variables if `pydantic-settings` fails to bundle in serverless runtimes.
   - Ensured static frontend directory resolution works across case-sensitive Linux filesystems (`Frontend`).
   - Added `from __future__ import annotations` and explicit `Tuple, Any` imports in [`agent/tools.py`](file:///c:/Users/Amey/Desktop/PeerSpace/agent/tools.py) for cross-version Python compatibility on AWS Lambda.
   - Ensured zero runtime disk writes: all persistence lives in Neon PostgreSQL and ephemeral in-RAM memory.

8. **Comprehensive Automated Test Coverage**:
   - 10/10 automated tests passing in [`tests/test_agent_orchestration.py`](file:///c:/Users/Amey/Desktop/PeerSpace/tests/test_agent_orchestration.py).
   - Ephemeral memory tracking tests passing in [`tests/test_agent_memory.py`](file:///c:/Users/Amey/Desktop/PeerSpace/tests/test_agent_memory.py).
   - Security audit tests passing in [`tests/test_security.py`](file:///c:/Users/Amey/Desktop/PeerSpace/tests/test_security.py).
