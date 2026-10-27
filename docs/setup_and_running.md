# PeerSpace: Setup & How to Run Locally

This guide walks you through setting up and running **PeerSpace** on your local machine in simple, step-by-step instructions.

---

## 📋 Prerequisites

Before starting, ensure you have the following installed on your machine:
- **Python 3.10+** (Python 3.11, 3.12, 3.13, or 3.14)
- **Node.js** (v18 or higher)
- **A Neon Serverless PostgreSQL Database** (or any PostgreSQL 14+ instance)

---

## 🛠️ Step-by-Step Setup Instructions

### Step 1: Open the Project Directory
Open your terminal (PowerShell, Command Prompt, or Bash) and navigate to the PeerSpace project folder:
```powershell
cd c:\Users\Amey\Desktop\PeerSpace
```

---

### Step 2: Set Up a Python Virtual Environment

Create and activate an isolated Python environment:

**On Windows (PowerShell):**
```powershell
# Create the virtual environment
python -m venv .venv

# Activate the virtual environment
.venv\Scripts\Activate.ps1
```

**On macOS / Linux:**
```bash
python3 -m venv .venv
source .venv/bin/activate
```

---

### Step 3: Install Dependencies

Install all required Python backend dependencies:
```powershell
pip install -r requirements.txt
```

*(Optional)* If you are building S3 file uploads, install the Node packages:
```powershell
npm install
```

---

### Step 4: Configure Environment Variables (`.env`)

PeerSpace includes a sanitized template file named [`.env.example`](file:///c:/Users/Amey/Desktop/PeerSpace/.env.example).

1. Copy `.env.example` to create your private `.env` file:
   ```powershell
   Copy-Item .env.example .env
   ```
2. Open `.env` and fill in your Neon PostgreSQL connection string:
   ```env
   # Neon Serverless PostgreSQL Connection String
   DATABASE_URL=postgresql://<username>:<password>@<endpoint-id>-pooler.<region>.aws.neon.tech/peerspace?sslmode=require&channel_binding=require

   # Security & Session Settings
   SECRET_KEY=generate_a_random_32_character_secret_key_here
   ENVIRONMENT=development
   PORT=8000
   ```

> [!NOTE]
> You do **not** need to manually rename `postgresql://` to `postgresql+psycopg://`. The backend's `pydantic-settings` engine in [`backend/config.py`](file:///c:/Users/Amey/Desktop/PeerSpace/backend/config.py) automatically converts it and enforces SSL.

---

### Step 5: Run Database Migrations

Apply the latest database schema migrations to create all 15 tables in your Neon database:

```powershell
# Run Alembic migrations
alembic upgrade head
```

---

### Step 6: Start the PeerSpace Server

Run the server with Python:

```powershell
python server.py
```

You should see log output similar to this:
```
INFO:     Started server process
INFO:     Waiting for application startup.
INFO:     Connecting to Neon Serverless PostgreSQL...
INFO:     Neon Serverless PostgreSQL connection initialized successfully.
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000 (Press CTRL+C to quit)
```

---

## 🔍 How to Verify Everything is Working

### 1. Test Database Connectivity
Open your browser or run this command in another terminal:
```powershell
curl http://localhost:8000/api/health
```

**Expected Result (HTTP 200)**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```
If the database connection is healthy, the backend confirms it with zero credential exposure.

---

### 2. Open the Web Application
Open your web browser and go to:
👉 **`http://localhost:8000/`**

- **Student Tab**: Try typing a message to the AI Coach (e.g., *"I have midterms tomorrow and I'm stressed"*). The AI will reply with a kind, 1–3 sentence friend response.
- **Counselor Tab**: Switch to the Counselor Portal to see active sessions and view the real-time AI reasoning stream.

---

## 🚨 Troubleshooting Common Issues

### Issue 1: Port 8000 is already in use (`WinError 10048`)
If an orphaned server process is still running from an earlier session:
```powershell
# Find the PID holding port 8000
netstat -ano | findstr :8000

# Kill the process (replace <PID> with the number from the last column)
taskkill /F /PID <PID>
```

### Issue 2: Event Loop Error with Psycopg on Windows
If you see `psycopg.InterfaceError: Event loop is closed`, ensure you start the server using:
```powershell
python server.py
```
`server.py` automatically configures Python to use the `SelectorEventLoop`, which is required for Psycopg 3 on Windows.

### Issue 3: Neon Connection Timeout / SSL Required
If the database fails to connect:
1. Verify that your Neon database is active (Neon databases pause when idle and automatically wake up within 2–3 seconds on the first query).
2. Check that your `.env` contains `sslmode=require`.
