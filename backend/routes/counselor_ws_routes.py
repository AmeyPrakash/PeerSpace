"""
Persistent WebSocket Routes for Student & Counselor direct communication.
"""

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.counselor_ws_manager import counselor_ws_manager

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
                # Forward to counselors
                await counselor_ws_manager.send_to_counselors({
                    "type": "student_chat_reply",
                    "session_id": session_id,
                    "message": data.get("message")
                })
            elif msg_type in ["offer", "answer", "ice-candidate", "mute-status"]:
                # Signal relay back to counselor for WebRTC
                await counselor_ws_manager.send_to_counselors({
                    "type": "student_webrtc_signal",
                    "session_id": session_id,
                    "signal": data
                })
    except WebSocketDisconnect:
        await counselor_ws_manager.disconnect_student(session_id)
    except Exception:
        await counselor_ws_manager.disconnect_student(session_id)

@router.websocket("/ws/counselor")
async def counselor_persistent_ws(websocket: WebSocket):
    # TODO: In production, require passkey authentication over WS or token.
    await websocket.accept()
    await counselor_ws_manager.connect_counselor(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            target_session = data.get("session_id")
            
            if not target_session:
                continue

            msg_type = data.get("type")
            if msg_type == "counselor_chat":
                await counselor_ws_manager.send_to_student(target_session, {
                    "type": "counselor_chat",
                    "message": data.get("message")
                })
            elif msg_type in ["offer", "answer", "ice-candidate", "mute-status"]:
                await counselor_ws_manager.send_to_student(target_session, {
                    "type": "counselor_webrtc_signal",
                    "signal": data
                })
    except WebSocketDisconnect:
        await counselor_ws_manager.disconnect_counselor(websocket)
    except Exception:
        await counselor_ws_manager.disconnect_counselor(websocket)
