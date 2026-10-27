# PeerSpace: AI Coach & Agent Documentation

This guide explains the **PeerSpace AI Coach (Agent)** in simple, everyday words—what it does, how it thinks, how its memory works, and how it protects student privacy.

---

## 🤖 What is the AI Coach in Simple Words?

The **AI Coach** is an anonymous conversational companion designed specifically for college students. 

When college life gets overwhelming—with exam pressure, relationship troubles, placement stress, or feeling lonely in a hostel room—students can open PeerSpace anytime (day or night) and just talk. 

Unlike a cold, robotic chatbot or an overly analytical therapist, the AI Coach talks like a **kind, understanding friend**:
- It listens without judging.
- It offers comfort and perspective first before trying to fix everything.
- It keeps its answers short, warm, and natural (1 to 3 sentences).
- It never pretends to be human or claims fake personal experiences.

---

## 🔄 How the AI Thinks: The Reasoning Loop

Before the AI Coach speaks, it doesn't just blurt out an answer. It runs through an internal step called the **Reasoning Loop**:

```
[ Student Sends Message ]
           │
           ▼
[ Step 1: Memory & Context Check ]
  - What has the student mentioned earlier? (e.g., upcoming exam, roommate issue)
  - What language are they using? (English, Hinglish, or Hindi?)
           │
           ▼
[ Step 2: Friend Perspective & Comfort ]
  - What actually happened? (Focus on the situation, not clinical labels)
  - What reassurance or perspective does the student need right now?
  - Does the student need a calming breathing exercise or immediate help?
           │
           ▼
[ Step 3: Quality & Anti-Therapist Check ]
  - Is the reply short (1 to 3 sentences)?
  - Did I avoid robotic clichés like "It sounds like you're feeling..."?
  - Did I separate the person's identity from their mistake?
           │
           ▼
[ Final Answer Sent to Student ]
```

### Real-Time Observability for Counselors
While the student **only** sees the kind, final message, the AI's internal reasoning is streamed live over WebSockets to the **On-Duty Campus Counselor Portal**. This allows human counselors to see how the student is doing in real-time and intervene if the student is in distress.

---

## 🧠 Ephemeral In-Memory System (Zero Disk Storage)

One of the biggest concerns students have is: *"Will my personal struggles be saved forever?"*

At PeerSpace, the answer is **no**:

> [!IMPORTANT]
> **Zero-Trace Privacy**: The AI Coach's memory lives **strictly inside computer RAM** while the chat is open. Nothing is written to the database or saved to files. When the student leaves or resets the chat, the memory vanishes completely.

### What the AI Remembers During the Active Chat:
1. **Language & Dialect**: Whether the student prefers English, Hinglish, or campus slang (e.g., "cooked", "fr", "tbh").
2. **Current Stressors**: Topics like exams, CGPA concerns, placement interviews, family expectations, or hostel living.
3. **Coping Tools Used**: Whether the student tried a 4-7-8 breathing exercise or a grounding technique earlier in the chat so it doesn't repeat suggestions.
4. **Emotional Trajectory**: Whether the student's mood is improving, staying steady, or escalating into acute distress.

---

## 💬 The "Kind Friend" Persona Rules

We configured the AI Coach to avoid sounding like a clinical textbook or a self-help article. Here are the core rules it follows:

### 1. Comfort & Perspective Over Emotion Labeling
- **Therapist Cliché (Banned)**: *"It sounds like you are experiencing severe performance anxiety. Would you like to explore where these feelings originate?"*
- **PeerSpace Friend (Used)**: *"It's okay—one bad test doesn't define who you are. What matters now is taking a breath and figuring out the next step together."*

### 2. Natural Hinglish & Language Matching
Indian college students frequently communicate in **Hinglish** (Hindi words spelled using the Roman alphabet, like *"bhai bohot tension ho rahi hai"*).
- If a student speaks in Hinglish, the AI responds in natural, warm Hinglish using the Roman alphabet (*"Bhai tension mat le, ek-ek step karke handle karenge"*).
- It never awkwardly switches into Hindi Devanagari script (हिंदी) unless the user specifically typed in Devanagari.

### 3. Short & Direct (1 to 3 Sentences)
- Friends don't send multi-paragraph essays or long bulleted lists when someone is venting.
- The AI keeps its replies focused on one supportive thought at a time.
- It does **not** force a question at the end of every message.

### 4. Human Friend Pivot (No Homework / No Coding)
Students might try to use the AI Coach as ChatGPT to solve homework or debug Python code. 
- The AI politely declines, but instead of saying robotic phrases like *"I am an AI language model trained by..."*, it pivots warmly like a friend:
  > *"I'm really not the right person for coding help, but it sounds like this assignment has you under a lot of stress. What's been the toughest part of it today?"*

---

## 🛡️ Safety & Crisis Guardrails

Safety is paramount on a campus platform. The AI Coach is equipped with automatic safety tools:

| Safety Tool | What It Does in Simple Words |
| :--- | :--- |
| **`crisis_safety_check`** | Detects words related to self-harm, severe despair, or crisis. Immediately provides 24/7 national and campus helpline contacts. |
| **`escalate_counselor_intervention`** | Alerts on-duty campus counselors instantly on their dashboard, flagging the student's session for human intervention. |
| **`mood_journal_tracker`** | Logs emotional check-in and mood triggers for the session. |

---

## ⚙️ Orchestration Architecture & Tool Calling Loop

The AI Coach is orchestrated by a robust execution engine in [`agent/agent.py`](file:///c:/Users/Amey/Desktop/PeerSpace/agent/agent.py):

1. **Pre-Generation Safety Fast-Path**:
   - Before invoking the LLM, the student's message is inspected for acute self-harm or crisis keywords.
   - If detected, the agent immediately alerts on-duty counselors (`CRITICAL` severity) and returns 24/7 helplines (**Tele-MANAS**: `14416`, **Jeevan Aastha**: `1800 233 3330`, **Aasra**: `09820466726`) in the student's language without waiting for LLM completion.

2. **ReAct Tool-Calling Loop & Budgeting**:
   - **Iteration Limit**: Capped at `MAX_ITERATIONS = 4` to prevent infinite loops.
   - **Tool Budget**: Capped at `MAX_TOOL_BUDGET = 3` total tool executions per turn.
   - **Zero-Tool Fast-Path**: If the student sends a casual message, the model answers directly with `Final Answer:` on step 1 with zero tool overhead.

3. **Tool Registry & Security Sandbox**:
   - Validates argument types and enforces length bounds (e.g. max 200–500 chars).
   - Enforces user authorization (students can only call authorized wellness tools).
   - Timeouts (4s per tool) and safe exception catching ensure tools never crash the application.

4. **Post-Generation Anti-Fabrication Guard**:
   - Inspects the generated response to detect fabricated action confirmations (e.g., falsely claiming to have booked an appointment or contacted a professor without executing a corresponding tool).
   - Safely reframes responses and strips internal reasoning directives.

---

## 📁 Related Source Files & Tests

- **Core Reasoning & Orchestration Agent**: [`agent/agent.py`](file:///c:/Users/Amey/Desktop/PeerSpace/agent/agent.py)
- **Tool Registry & Secure Execution**: [`agent/tools.py`](file:///c:/Users/Amey/Desktop/PeerSpace/agent/tools.py)
- **Prompts & Persona Rules**: [`agent/prompts.py`](file:///c:/Users/Amey/Desktop/PeerSpace/agent/prompts.py)
- **In-RAM Ephemeral Memory**: [`agent/memory.py`](file:///c:/Users/Amey/Desktop/PeerSpace/agent/memory.py)
- **Automated Orchestration Test Suite**: [`tests/test_agent_orchestration.py`](file:///c:/Users/Amey/Desktop/PeerSpace/tests/test_agent_orchestration.py)
