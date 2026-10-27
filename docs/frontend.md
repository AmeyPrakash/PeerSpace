# PeerSpace: Frontend & Counselor Portal Documentation

This document explains the **PeerSpace Web Frontend** in simple, clear words—how the screens are designed, how students interact with the platform, what the on-duty counselor sees, and recent improvements made to protect student privacy.

---

## 🎨 Design Philosophy & Soothing Aesthetics

Mental health platforms should feel comforting, not clinical, cold, or sterile. 

PeerSpace's frontend uses a calming, pastel color palette designed to reduce anxiety:
- **Soft Muted Colors**: Sage greens, gentle blues, lavender accents, and warm off-white surfaces.
- **Light & Dark Mode**: One-click theme switcher that automatically remembers the student's preference in `localStorage`.
- **Zero-Friction Anonymity**: No forced registration for venting. When a student visits the site, they are immediately assigned a friendly, anonymous identity (like `MindfulOtter42` or `QuietRiver66`).

---

## 📱 Main Screens & Views

The frontend is built as a fast, responsive Single Page Application (HTML5, Vanilla CSS, and JavaScript in [`Frontend/js/app.js`](file:///c:/Users/Amey/Desktop/PeerSpace/Frontend/js/app.js)):

```
                                [ PeerSpace Top Navigation ]
                                      /              \
                                     /                \
                       [ 🎓 Student View ]     [ 🩺 Counselor Portal ]
                              │                         │
             ┌────────────────┴──────────────┐          │
             ▼                               ▼          ▼
     [ AI Coach Chat ]             [ WebRTC Voice ]  [ Live Alerts & Sessions ]
     - Mood / Stressor Chips       - Peer Pairing    - Live AI Reasoning Stream
     - Breathing Exercises         - Call Controls   - Direct 1-Click Takeover
```

---

### 1. The Student Portal

The Student Portal is the welcoming home screen for campus members:

1. **Anonymous Hero Header**:
   - Greets the student by their anonymous handle.
   - Includes quick action buttons: *"Talk to AI Coach"*, *"Anonymous Voice Call"*, and *"Connect with Human Counselor"*.

2. **AI Coach Chat Stream**:
   - Natural, speech-bubble interface.
   - Typing indicator so the student knows the AI is actively listening and thinking.
   - Formatted markdown rendering for readable, clean text.

3. **Quick Mood & Stressor Chips**:
   - Single-tap prompts for common student situations (e.g., *"Midterm stress"*, *"Roommate argument"*, *"Feeling isolated"*, *"Need a breathing exercise"*).
   - Allows students who feel overwhelmed to start a conversation without having to type out long sentences.

4. **Calming Exercise Modal**:
   - Interactive guides for **Box Breathing**, **4-7-8 Breathing**, and **5-4-3-2-1 Sensory Grounding**.
   - Includes gentle visual animations that expand and contract to help students pace their breath.

5. **Peer-to-Peer Voice Call Overlay**:
   - A minimalist, distraction-free voice interface for students who prefer speaking over typing.
   - Displays mute/unmute buttons, call timer, and safe disconnect button.
   - Uses direct WebRTC peer connections so audio never records to a server.

---

### 2. The Counselor Portal

The Counselor Portal is a secure view built for verified, on-duty campus counselors:

1. **Live Safety Alert Counter**:
   - A prominent badge in the top navigation updates in real time whenever an emergency alert is triggered.
   - Red and orange alerts identify students who may need immediate outreach or human check-in.

2. **Active Sessions Monitor**:
   - Lists active student conversations across campus.
   - Counselors can click any session to view the transcript in real time.

3. **Live AI Reasoning Stream**:
   - Displays the internal reasoning step of the AI Coach (*"Reasoning: Analyzes information and decides what to do..."*).
   - Shows counselors why the AI chose a specific response and what context it considered.

4. **Human Counselor Intervention**:
   - If a counselor sees that a student needs professional human care, they can click the **Intervene** button.
   - The AI is instantly muted, and the student's chat transitions directly into a human-to-human counseling conversation.

---

## 🧹 Privacy Polish: Removal of the Student Memory Profile Card

In an earlier prototype, the counselor window displayed an internal diagnostic panel:
```
🧠 Student Memory & Context Profile
Language: English
COPING TOOLS TRIED: 🌿 Deep Breathing Technique, 🌿 Sensory Grounding
EMOTIONAL TRAJECTORY: 📈 High Stress & Anxiety
```

### Why We Removed It:
1. **Privacy First**: Raw internal memory tags and psychological labels shouldn't be stamped on a student like a medical diagnosis.
2. **Cleaner Interface**: Counselors reported that the memory card cluttered their screen and distracted from the actual conversation.
3. **What Changed in Code**:
   - In [`Frontend/js/app.js`](file:///c:/Users/Amey/Desktop/PeerSpace/Frontend/js/app.js), we stripped the `memCard` HTML generation and removed memory chip injection into the counselor transcript.
   - Counselors now have an unobstructed, clean view of the conversation, while the live AI reasoning stream remains available in its dedicated panel for safety tracking.

---

## 📁 Related Source Files

- **HTML Structure**: [`Frontend/index.html`](file:///c:/Users/Amey/Desktop/PeerSpace/Frontend/index.html)
- **Application Logic**: [`Frontend/js/app.js`](file:///c:/Users/Amey/Desktop/PeerSpace/Frontend/js/app.js)
- **Styling & Pastel Themes**: [`Frontend/css/style.css`](file:///c:/Users/Amey/Desktop/PeerSpace/Frontend/css/style.css)
