import logging
from fastapi import APIRouter, WebSocket, WebSocketDisconnect, status
from backend.counselor_ws_manager import counselor_ws_manager
from backend.security import verify_passkey
from backend.config import COUNSELOR_PASSKEY_HASH
from backend.session_manager import set_counselor_active, sessions

logger = logging.getLogger("peerspace.counselor_ws_routes")

router = APIRouter(tags=["counselor_ws"])

@router.websocket("/ws/student")
async def student_persistent_ws(websocket: WebSocket):
    session_id = websocket.query_params.get("session_id")
    if not session_id:
        await websocket.close()
        return

    await websocket.accept()
    await counselor_ws_manager.connect_student(websocket, session_id)
    try:
        while True:
            # We keep the connection alive. Students mainly receive data here,
            # but can also reply to counselor chats via WS.
            data = await websocket.receive_json()
            msg_type = data.get("type")
            
            if msg_type == "chat_reply":
                effective_sid = str(data.get("session_id") or session_id).strip()
                alias = data.get("alias", "Student")
                msg_id = data.get("msg_id")
                msg_text = data.get("message", "")

                # Mark session active with counselor intervention
                set_counselor_active(effective_sid, True)
                if effective_sid in sessions:
                    sessions[effective_sid].message_count += 1
                    try:
                        sessions[effective_sid].agent.add_message("user", msg_text)
                    except Exception:
                        pass

                logger.info("Forwarding student_chat_reply from session %s (%s, msg_id=%s) to %d counselor(s)", effective_sid, alias, msg_id, len(counselor_ws_manager.active_counselors))
                # Forward to counselors
                await counselor_ws_manager.send_to_counselors({
                    "type": "student_chat_reply",
                    "msg_id": msg_id,
                    "session_id": effective_sid,
                    "alias": alias,
                    "message": msg_text
                })
            elif msg_type in ["offer", "answer", "ice-candidate", "mute-status", "peer_disconnected"]:
                # Signal relay back to counselor for WebRTC
                await counselor_ws_manager.send_to_counselors({
                    "type": "student_webrtc_signal",
                    "session_id": session_id,
                    "signal": data
                })
            elif msg_type in ["student_voice_accept", "student_voice_decline"]:
                await counselor_ws_manager.send_to_counselors({
                    "type": msg_type,
                    "session_id": session_id
                })
    except WebSocketDisconnect:
        await counselor_ws_manager.disconnect_student(session_id, websocket)
    except Exception:
        await counselor_ws_manager.disconnect_student(session_id, websocket)

@router.websocket("/ws/counselor")
async def counselor_persistent_ws(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token or not verify_passkey(token, COUNSELOR_PASSKEY_HASH):
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION)
        return

    await websocket.accept()
    await counselor_ws_manager.connect_counselor(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            target_session = data.get("session_id")
            
            if not target_session:
                continue

            msg_type = data.get("type")
            if msg_type in ["counselor_chat", "counselor_voice_join", "counselor_join_text"]:
                counselor_ws_manager.register_counselor_session(websocket, target_session)
                set_counselor_active(target_session, True)
                if msg_type == "counselor_chat" and data.get("message"):
                    if target_session in sessions:
                        try:
                            sessions[target_session].agent.add_message("assistant", f"[COUNSELOR]: {data.get('message')}")
                        except Exception:
                            pass
                    await counselor_ws_manager.send_to_student(target_session, {
                        "type": "counselor_chat",
                        "message": data.get("message")
                    })
                elif msg_type == "counselor_voice_join":
                    if target_session in sessions:
                        try:
                            sessions[target_session].agent.add_message("assistant", "[COUNSELOR JOINED LIVE VOICE CALL]")
                        except Exception:
                            pass
                    await counselor_ws_manager.send_to_student(target_session, {
                        "type": "counselor_join_voice"
                    })
                else:
                    await counselor_ws_manager.send_to_student(target_session, {
                        "type": "counselor_join_text"
                    })
            elif msg_type in ["offer", "answer", "ice-candidate", "mute-status", "peer_disconnected"]:
                await counselor_ws_manager.send_to_student(target_session, {
                    "type": "counselor_webrtc_signal",
                    "signal": data
                })
            elif msg_type == "counselor_voice_invite":
                await counselor_ws_manager.send_to_student(target_session, {
                    "type": "counselor_voice_invite"
                })
            elif msg_type == "counselor_leave_text":
                logger.info("Counselor ending live text session with student %s", target_session)
                counselor_ws_manager.unregister_counselor_session(websocket, target_session)
                set_counselor_active(target_session, False)
                if target_session in sessions:
                    try:
                        sessions[target_session].agent.add_message("assistant", "[COUNSELOR ENDED INTERVENTION]")
                    except Exception:
                        pass
                await counselor_ws_manager.send_to_student(target_session, {
                    "type": "counselor_leave_text"
                })
    except WebSocketDisconnect:
        await counselor_ws_manager.disconnect_counselor(websocket)
    except Exception:
        await counselor_ws_manager.disconnect_counselor(websocket)
