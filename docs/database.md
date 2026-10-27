# PeerSpace: Database & Storage Documentation

This document explains the **PeerSpace Database Architecture**, the **Neon Serverless PostgreSQL** setup, and provides a **detailed, plain-English explanation of exactly what data the database stores**.

---

## 🏗️ Database Overview

PeerSpace uses **Neon Serverless PostgreSQL** (PostgreSQL 18.6 running on AWS `us-east-2`). 

- **Serverless Scaling**: Compute automatically adjusts to traffic and scales down to zero when idle to save costs.
- **Connection Pooling**: Uses Neon's built-in **PgBouncer** in transaction pooling mode via the `-pooler` connection string.
- **Driver**: Modern **Psycopg 3** (`psycopg[binary]`) with SQLAlchemy 2.0 async engine (`postgresql+psycopg://`).
- **SSL**: Native encrypted transport enforced (`sslmode=require&channel_binding=require`).

---

## 📦 What the Database Stores (Detailed Breakdown)

PeerSpace organizes its persistent data into **15 structured tables**. Here is what each table stores in simple words:

```
                                  [ users ]
                                  /       \
                     1:1         /         \ 1:1
                                v           v
               [ student_profiles ]       [ counselor_profiles ]
                  /        |     \                |         \
                 /         |      \               |          \
                v          v       v              v           v
    [ appointments ] [ assessments ] [ community_posts ] [ documents ]
           ^                               ^
           |                               |
    [ counselor_id ]               [ post_comments ]
```

---

### 1. `users` (Account Credentials & Roles)
Stores base account access data for registered campus members:
- **`id`**: Unique user ID (UUIDv4).
- **`email`**: User's campus or personal email address (unique, indexed).
- **`password_hash`**: Securely hashed password (bcrypt). Plain passwords are never stored.
- **`role`**: User type (`student`, `counselor`, or `admin`).
- **`is_active`**: Boolean indicating if the account is currently enabled.
- **`email_verified`**: Boolean indicating if the user confirmed their email via OTP.
- **`last_login`**: Timestamp of the user's most recent login.
- **`created_at` / `updated_at`**: Timestamps tracking account creation and edits.

---

### 2. `student_profiles` (Anonymous Student Identities)
Stores student background details while strictly guarding anonymity:
- **`id`**: Profile ID (UUIDv4).
- **`user_id`**: Links to the `users` table.
- **`anonymous_id`**: Randomly generated privacy handle (e.g., `MindfulOtter42`, `QuietRiver66`) displayed publicly instead of the student's real name.
- **`college_name`**: Institution name for campus-specific resources.
- **`academic_year`**: Current year of study (e.g., `Freshman`, `Sophomore`, `Final Year`).
- **`preferred_language`**: Preferred language for support (e.g., `English`, `Hinglish`, `Hindi`).

---

### 3. `counselor_profiles` (Verified Campus Counselors)
Stores information about professional counselors approved to provide mental health care:
- **`id`**: Counselor ID (UUIDv4).
- **`user_id`**: Links to the `users` table.
- **`full_name`**: Real, verified name of the licensed counselor.
- **`specialization`**: Areas of mental health expertise (e.g., `Academic Burnout`, `Clinical Anxiety`, `Trauma`).
- **`qualification`**: Professional degrees (e.g., `M.A. Clinical Psychology`, `Licensed Therapist`).
- **`experience_years`**: Total years of clinical or campus counseling experience.
- **`bio`**: Counselor's self-introduction and approach to therapy.
- **`verification_status`**: Current vetting state (`pending`, `approved`, or `rejected`).
- **`verified_at`**: Timestamp when an administrator approved the counselor.

---

### 4. `counselor_verification_documents` (Counselor Credentials)
Stores verification records for credentials submitted during counselor onboarding:
- **`id`**: Document record ID (UUIDv4).
- **`counselor_id`**: Links to `counselor_profiles`.
- **`document_url`**: Secure S3 storage URL pointing to the uploaded certificate, license, or diploma.
- **`document_type`**: Type of document uploaded (e.g., `Government ID`, `Degree Certificate`, `Medical License`).
- **`uploaded_at`**: Timestamp of upload.
- **`review_notes`**: Admin feedback or verification notes.
- **`status`**: Approval status of the document (`pending`, `approved`, or `rejected`).

---

### 5. `counselor_applications` (Prospective Counselor Submissions)
Stores application submissions from mental health professionals applying to join PeerSpace:
- **`application_id`**: Human-readable tracking code (e.g., `APP-2026-X79`).
- **`full_name`**, **`email`**, **`phone`**: Contact details of the applicant.
- **`highest_degree`**, **`degree_field`**, **`university`**, **`graduation_year`**: Academic background.
- **`certifications`**, **`years_of_experience`**, **`current_role`**: Professional credentials.
- **`specializations`**, **`motivation`**, **`background_info`**: Detailed statement of intent and expertise.
- **`status`**: Application state (`pending`, `approved`, `rejected`).
- **`reviewed_at`**, **`reviewer_notes`**: Audit trail of who reviewed the application and why.

---

### 6. `appointments` (Scheduled 1-on-1 Counseling Sessions)
Stores scheduled appointments between students and counselors:
- **`id`**: Appointment ID (UUIDv4).
- **`student_id`**: Links to `student_profiles`.
- **`counselor_id`**: Links to `counselor_profiles`.
- **`appointment_datetime`**: Scheduled date and time of the session.
- **`status`**: Current session state (`pending`, `confirmed`, `completed`, `cancelled`).
- **`session_notes`**: Private notes documented by the counselor after the appointment.
- *Constraint*: A database constraint ensures a student and counselor cannot book the exact same time slot twice (`unique_appointment_slot`).

---

### 7. `conversations` (Human-to-Human Counseling Chat Sessions)
Stores chat sessions between a student and a human counselor:
- **`id`**: Conversation ID (UUIDv4).
- **`student_id`**: Links to `student_profiles`.
- **`counselor_id`**: Links to `counselor_profiles`.
- **`status`**: State of the chat (`active` or `closed`).
- *Constraint*: A unique index enforces that a student and counselor can only have one `active` conversation at any given time.

---

### 8. `messages` (Messages in Human Counseling Sessions)
Stores individual chat messages sent in human-to-human counseling sessions:
- **`id`**: Message ID (UUIDv4).
- **`conversation_id`**: Links to `conversations`.
- **`sender_user_id`**: Links to the `users` account that sent the message.
- **`message_content`**: The text content of the message.
- **`is_read`**: Boolean flag showing if the recipient has read the message.
- **`created_at`**: Timestamp when the message was sent.

---

### 9. `mental_health_assessments` (Wellness Screenings)
Stores standardized, self-guided mental health assessment scores taken by students:
- **`id`**: Assessment result ID (UUIDv4).
- **`student_id`**: Links to `student_profiles`.
- **`assessment_type`**: Screening category (`stress`, `anxiety`, `depression`, `peer_pressure`).
- **`score`**: Numerical score calculated from standard screening questions (e.g. PHQ-9 or GAD-7).
- **`risk_level`**: Calculated risk classification (`low`, `medium`, `high`).
- **`created_at`**: Date and time the assessment was completed.

---

### 10. `crisis_alerts` (Emergency Safety Escalations)
Stores alerts created when a student is detected in immediate emotional distress or crisis:
- **`id`**: Crisis alert ID (UUIDv4).
- **`student_id`**: Links to `student_profiles`.
- **`counselor_id`**: Links to the counselor assigned to triage the emergency (if assigned).
- **`assessment_id`**: Links to the assessment that triggered the alert (if triggered via screening).
- **`severity`**: Urgency level (`low`, `medium`, `high`, `critical`).
- **`status`**: Triage state (`pending`, `in_progress`, `resolved`, `false_alarm`).
- **`created_at`** / **`resolved_at`**: Timestamps for audit tracking and response time metrics.

---

### 11. `community_posts` (Peer Support Forum Posts)
Stores public or anonymous forum discussions shared with the campus community:
- **`id`**: Post ID (UUIDv4).
- **`student_id`**: Links to `student_profiles`.
- **`title`**: Discussion headline (e.g., *"Dealing with exam anxiety in 3rd year"*).
- **`content`**: Full body text of the student's post.
- **`likes_count`**: Counter of peer encouragement / upvotes received.
- **`created_at` / `updated_at`**: Timestamps.

---

### 12. `post_comments` (Community Discussion Replies)
Stores supportive replies and comments made under forum posts:
- **`id`**: Comment ID (UUIDv4).
- **`post_id`**: Links to `community_posts`.
- **`student_id`**: Links to `student_profiles` (the author of the comment).
- **`content`**: Comment text.
- **`created_at`**: Timestamp of the reply.

---

### 13. `reports` (Community Moderation & Safety Reports)
Stores reports submitted by users flagging harmful content or harassment:
- **`id`**: Report ID (UUIDv4).
- **`reporter_user_id`**: Links to `users` (the account that reported the item).
- **`target_type`**: Type of content being reported (e.g., `post`, `comment`, `user`).
- **`target_id`**: ID of the reported entity.
- **`reason`**: Explanation provided by the reporter (e.g., *"Inappropriate language"* or *"Harassment"*).
- **`status`**: Review state (`pending`, `reviewed`, `action_taken`, `dismissed`).

---

### 14. `notifications` (User Alerts)
Stores in-app alerts and reminders for students and counselors:
- **`id`**: Notification ID (UUIDv4).
- **`user_id`**: Recipient user account.
- **`title`**: Brief headline (e.g., *"Appointment Confirmed"*).
- **`message`**: Notification message body.
- **`is_read`**: Boolean tracking whether the user opened the notification.
- **`created_at`**: Timestamp.

---

### 15. `verification_otps` (Security One-Time Passwords)
Stores temporary, expiring OTP codes used during registration, email verification, or counselor sign-up:
- **`id`**: OTP record ID (UUIDv4).
- **`target`**: The destination email address or phone number.
- **`contact_type`**: Destination medium (`email` or `phone`).
- **`otp_code`**: 6-digit numeric verification code.
- **`expires_at`**: Strict expiration time (typically 5 to 10 minutes from creation).
- **`created_at`**: Generation timestamp.

---

## 🔒 What the Database DOES NOT Store (Privacy Guarantee)

A core pillar of PeerSpace is student trust and zero retention:

> [!IMPORTANT]
> **Student chats with the AI Coach are NEVER saved to the database.**
> Conversations with the AI Coach reside purely in memory (RAM) while the student's session is open. When the session finishes or is reset, the in-memory context is destroyed. No text, stressors, or emotional trajectories from AI chat are permanently stored on disk.

---

## ⚙️ Connection Architecture & Code Integration

### Connection String Setup in `.env`
In your `.env` file, configure the pooled connection string:
```env
DATABASE_URL=postgresql://<username>:<password>@<endpoint-id>-pooler.<region>.aws.neon.tech/peerspace?sslmode=require&channel_binding=require
```

### Automatic URL Normalization (`backend/config.py`)
FastAPI uses `pydantic-settings` to automatically validate and normalize the URL:
- Strips `postgresql://` and converts it to `postgresql+psycopg://` so SQLAlchemy uses the async Psycopg 3 driver.
- Enforces `sslmode=require` for Neon cloud endpoints.

### Reusable Database Session (`backend/database.py`)
FastAPI route endpoints access the database by declaring `db: AsyncSession = Depends(get_db)`:
```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db

router = APIRouter()

@router.get("/my-endpoint")
async def my_endpoint(db: AsyncSession = Depends(get_db)):
    # Reusable session is automatically created and cleanly closed
    ...
```

### Alembic Migrations
Migrations are handled via Alembic in [`migrations/`](file:///c:/Users/Amey/Desktop/PeerSpace/migrations):
- **Direct Endpoint Routing**: Migrations automatically use the direct Neon compute URL (stripping `-pooler`) so database locks and DDL changes run without PgBouncer pooler conflicts.
- **Commands**:
  ```powershell
  # Check current revision
  alembic current

  # Upgrade database to latest revision
  alembic upgrade head
  ```
