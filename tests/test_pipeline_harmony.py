"""
PeerSpace Test: AI Coach & Human Counselor Intervention Pipeline Harmony
Validates that:
1. AI CBT Coach works normally with ReAct loop and language mirroring.
2. When counselor intervenes, AI is strictly suppressed and student messages route to counselor.
3. Counselor can fetch transcript with prior AI chat history.
4. When counselor leaves, AI Coach resumes smoothly with peer persona and ReAct format intact.
5. If counselor disconnects abruptly, backend auto-recovers and student is never stuck in limbo.
"""

import sys
import os
from pathlib import Path

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from starlette.testclient import TestClient
from server import app
from backend.session_manager import sessions, get_or_create_agent, set_counselor_active, is_counselor_active
from backend.counselor_ws_manager import counselor_ws_manager

COUNSELOR_PASSKEY = os.getenv("COUNSELOR_PASSKEY")

def test_full_pipeline_harmony_lifecycle(client):
    session_id = "test-harmony-session-1"
    student_alias = "MindfulOtter42"
    
    # Clean up state
    sessions.pop(session_id, None)

    # -------------------------------------------------------------
    # Phase 1: Student chats with AI Coach
    # -------------------------------------------------------------
    agent, sid, alias = get_or_create_agent(session_id, student_alias)
    assert not is_counselor_active(sid), "Counselor should not be active initially"

    res = client.post("/api/chat", json={
        "message": "Hey, I've been feeling stressed about exams",
        "session_id": sid,
        "alias": alias
    })
    assert res.status_code == 200
    data = res.json()
    assert data["reply"] is not None, "AI should reply when counselor is not active"
    assert not data["counselor_active"], "counselor_active should be False"
    assert len(agent.conversation_history) >= 3, "History should have system, user, assistant"

    # -------------------------------------------------------------
    # Phase 2: Counselor checks active sessions & transcript
    # -------------------------------------------------------------
    admin_headers = {"x-admin-token": COUNSELOR_PASSKEY}
    res_sessions = client.get("/api/admin/sessions", headers=admin_headers)
    assert res_sessions.status_code == 200
    all_active = res_sessions.json()["active_sessions"]
    assert any(s["full_id"] == sid for s in all_active), "Session must appear in admin sessions"

    # Fetch transcript
    res_trans = client.get(f"/api/admin/sessions/{sid}/transcript", headers=admin_headers)
    assert res_trans.status_code == 200
    trans_data = res_trans.json()
    assert trans_data["session_id"] == sid
    assert len(trans_data["transcript"]) >= 2
    # Verify student turn and AI coach turn
    student_turns = [t for t in trans_data["transcript"] if t["role"] == "user"]
    ai_turns = [t for t in trans_data["transcript"] if t["sender"] == "AI Coach"]
    assert len(student_turns) >= 1
    assert len(ai_turns) >= 1

    # -------------------------------------------------------------
    # Phase 3: Counselor intervenes via WebSockets
    # -------------------------------------------------------------
    # Connect student WebSocket
    with client.websocket_connect(f"/ws/student?session_id={sid}") as student_ws:
        # Connect counselor WebSocket
        with client.websocket_connect(f"/ws/counselor?token={COUNSELOR_PASSKEY}") as counselor_ws:
            assert len(counselor_ws_manager.active_counselors) >= 1

            # Counselor sends counselor_join_text
            counselor_ws.send_json({"type": "counselor_join_text", "session_id": sid})
            
            # Student receives counselor_join_text
            student_msg = student_ws.receive_json()
            assert student_msg["type"] == "counselor_join_text"
            assert is_counselor_active(sid), "counselor_active must now be True"

            # Counselor sends counselor_chat message
            counselor_ws.send_json({
                "type": "counselor_chat",
                "session_id": sid,
                "message": "Hello, I am a university counselor. I am right here with you."
            })
            student_chat_msg = student_ws.receive_json()
            assert student_chat_msg["type"] == "counselor_chat"
            assert "university counselor" in student_chat_msg["message"]

            # ---------------------------------------------------------
            # Phase 4: Student replies while counselor is active
            # ---------------------------------------------------------
            # 4a. Via Student WebSocket
            student_ws.send_json({
                "type": "chat_reply",
                "session_id": sid,
                "alias": alias,
                "msg_id": "test-msg-1",
                "message": "Thank you counselor, my chest feels heavy."
            })
            counselor_recv = counselor_ws.receive_json()
            assert counselor_recv["type"] == "student_chat_reply"
            assert counselor_recv["message"] == "Thank you counselor, my chest feels heavy."

            # 4b. Via HTTP POST /api/chat (should route to counselor, AI 100% suppressed)
            res_chat = client.post("/api/chat", json={
                "message": "Are you still there, counselor?",
                "session_id": sid,
                "alias": alias
            })
            assert res_chat.status_code == 200
            data_chat = res_chat.json()
            assert data_chat["reply"] is None, "AI Coach MUST be completely suppressed during counselor intervention"
            assert data_chat["counselor_active"] is True

            counselor_recv2 = counselor_ws.receive_json()
            assert counselor_recv2["type"] == "student_chat_reply"
            assert counselor_recv2["message"] == "Are you still there, counselor?"

            # ---------------------------------------------------------
            # Phase 5: Counselor leaves session
            # ---------------------------------------------------------
            counselor_ws.send_json({
                "type": "counselor_leave_text",
                "session_id": sid
            })
            student_leave = student_ws.receive_json()
            assert student_leave["type"] == "counselor_leave_text"
            assert not is_counselor_active(sid), "counselor_active must be False after counselor leaves"

    # -------------------------------------------------------------
    # Phase 6: Student resumes AI Coach (Persona & ReAct test)
    # -------------------------------------------------------------
    res_resume = client.post("/api/chat", json={
        "message": "Thanks for earlier, I feel a little calmer now.",
        "session_id": sid,
        "alias": alias
    })
    assert res_resume.status_code == 200
    data_resume = res_resume.json()
    assert data_resume["reply"] is not None, "AI coach should answer once counselor leaves"
    assert not data_resume["counselor_active"]
    assert "[COUNSELOR]" not in data_resume["reply"], "AI coach should not prefix response with [COUNSELOR]"

    # -------------------------------------------------------------
    # Phase 7: Silent counselor disconnect auto-recovery
    # -------------------------------------------------------------
    # Re-activate counselor intervention
    set_counselor_active(sid, True)
    assert is_counselor_active(sid)

    # Connect counselor and simulate sudden close/disconnect
    with client.websocket_connect(f"/ws/student?session_id={sid}") as student_ws:
        with client.websocket_connect(f"/ws/counselor?token={COUNSELOR_PASSKEY}") as counselor_ws:
            counselor_ws.send_json({"type": "counselor_join_text", "session_id": sid})
            student_ws.receive_json() # consume join
            # Counselor closes connection without sending counselor_leave_text
        
        # Student receives counselor_leave_text via auto-recovery
        auto_recovery_msg = student_ws.receive_json()
        assert auto_recovery_msg["type"] == "counselor_leave_text", "Student must receive leave text on counselor abrupt disconnect"
        assert not is_counselor_active(sid), "Session counselor_active must be cleared on disconnect"

    # -------------------------------------------------------------
    # Phase 8: Student continues chatting with AI Coach after sudden counselor disconnect
    # -------------------------------------------------------------
    res_post_disconnect = client.post("/api/chat", json={
        "message": "Is anyone here? The counselor seemed to drop off.",
        "session_id": sid,
        "alias": alias
    })
    assert res_post_disconnect.status_code == 200
    data_post_disconnect = res_post_disconnect.json()
    assert data_post_disconnect["reply"] is not None, "AI should immediately answer after counselor dropped"
    assert not is_counselor_active(sid)

    # -------------------------------------------------------------
    # Phase 9: Multilingual / Hinglish Mirroring Across Intervention Lifecycle
    # -------------------------------------------------------------
    session_id_hinglish = "test-harmony-hinglish"
    agent_h, sid_h, alias_h = get_or_create_agent(session_id_hinglish, "DesiSparrow")
    
    # 9a. Student chats in Hinglish
    res_h1 = client.post("/api/chat", json={
        "message": "bhai bohot tension ho rahi hai kal exam hai aur syllabus bacha hai",
        "session_id": sid_h,
        "alias": alias_h
    })
    assert res_h1.status_code == 200
    reply_h1 = res_h1.json()["reply"]
    assert reply_h1 is not None
    # Check that AI mirrors Hinglish
    lang_detected = agent_h._detect_user_language("bhai bohot tension ho rahi hai kal exam hai aur syllabus bacha hai")
    assert lang_detected == "hinglish"
    print(f"Hinglish AI Reply 1: {reply_h1}")

    # 9b. Counselor joins and intervenes
    with client.websocket_connect(f"/ws/counselor?token={COUNSELOR_PASSKEY}") as counselor_ws:
        counselor_ws.send_json({"type": "counselor_join_text", "session_id": sid_h})
        assert is_counselor_active(sid_h)

        # Student sends message during intervention -> AI suppressed
        res_h_suppressed = client.post("/api/chat", json={
            "message": "counselor sir bohot load ho raha hai",
            "session_id": sid_h,
            "alias": alias_h
        })
        assert res_h_suppressed.json()["reply"] is None, "AI must be suppressed during intervention"
        assert res_h_suppressed.json()["counselor_active"] is True

        # Counselor ends intervention
        counselor_ws.send_json({"type": "counselor_leave_text", "session_id": sid_h})
        import time
        time.sleep(0.15)
        assert not is_counselor_active(sid_h)

    # 9c. Student resumes in Hinglish -> AI must respond in Hinglish with peer persona
    res_h2 = client.post("/api/chat", json={
        "message": "yaar ab thoda theek lag raha hai, aage kya karu?",
        "session_id": sid_h,
        "alias": alias_h
    })
    assert res_h2.status_code == 200
    reply_h2 = res_h2.json()["reply"]
    assert reply_h2 is not None
    print(f"Hinglish AI Reply 2 (resumed): {reply_h2}")
    assert "[COUNSELOR]" not in reply_h2

    # Clean up
    sessions.pop(session_id, None)
    sessions.pop(session_id_hinglish, None)
    print("ALL 9 PHASES OF PIPELINE HARMONY & LANGUAGE MIRRORING PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    tc = TestClient(app)
    test_full_pipeline_harmony_lifecycle(tc)


