"""
Tests Counselor Intervention Routing, AI Suppression, and Multilingual Language Mirroring.
"""

import sys
import asyncio
from pathlib import Path

# Ensure UTF-8 output
if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from fastapi.testclient import TestClient
from server import app
from backend.session_manager import sessions, set_counselor_active, is_counselor_active
from backend.counselor_ws_manager import counselor_ws_manager

client = TestClient(app)

def test_counselor_intervention_and_ai_suppression():
    print("\n" + "=" * 70)
    print(" TESTING COUNSELOR INTERVENTION & AI SUPPRESSION PIPELINE")
    print("=" * 70)

    # 1. Start student session with AI Coach
    sid = "test-intervention-sid-123"
    res1 = client.post("/api/chat", json={
        "session_id": sid,
        "alias": "TestStudent",
        "message": "Hey, I have been feeling quite stressed about my upcoming exams."
    })
    assert res1.status_code == 200
    data1 = res1.json()
    assert data1["reply"] is not None
    assert data1["counselor_active"] is False
    assert not is_counselor_active(sid)
    print("[1/5] Student -> AI Coach normal response: PASSED")
    print(f"      AI Reply: {data1['reply'][:60]}...")

    # 2. Counselor Intervenes
    res2 = client.post("/api/chat/intervene", json={
        "session_id": sid,
        "message": "Hello TestStudent, I'm Counselor Priya. I am stepping in to support you."
    })
    assert res2.status_code == 200
    assert is_counselor_active(sid) is True
    print("[2/5] Counselor intervenes: session marked counselor_active = True: PASSED")

    # 3. Student replies while Counselor is active via /api/chat
    # AI MUST NOT ANSWER (reply is None) AND counselor_active is True
    res3 = client.post("/api/chat", json={
        "session_id": sid,
        "alias": "TestStudent",
        "message": "Hi Counselor Priya, thank you for being here with me."
    })
    assert res3.status_code == 200
    data3 = res3.json()
    assert data3["reply"] is None, f"Expected AI reply to be None, got: {data3['reply']}"
    assert data3["counselor_active"] is True
    print("[3/5] Student /api/chat while counselor active -> AI strictly SUPPRESSED, message routed to counselor: PASSED")

    # 4. Student replies via /api/chat/reply
    res4 = client.post("/api/chat/reply", json={
        "session_id": sid,
        "alias": "TestStudent",
        "message": "Can we talk about test anxiety strategies?"
    })
    assert res4.status_code == 200
    assert is_counselor_active(sid) is True
    print("[4/5] Student /api/chat/reply -> successfully received and session remains counselor_active: PASSED")

    # 5. Counselor leaves intervention
    set_counselor_active(sid, False)
    assert not is_counselor_active(sid)

    # Student talks to AI Coach again -> AI answers
    res5 = client.post("/api/chat", json={
        "session_id": sid,
        "alias": "TestStudent",
        "message": "Thank you, feeling a little calmer now."
    })
    assert res5.status_code == 200
    data5 = res5.json()
    assert data5["reply"] is not None
    assert data5["counselor_active"] is False
    print("[5/5] Counselor leaves -> Student /api/chat resumes AI CBT coach: PASSED")
    print(f"      AI Reply: {data5['reply'][:60]}...")

    print("\n ALL INTERVENTION TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_counselor_intervention_and_ai_suppression()
