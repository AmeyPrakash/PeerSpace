"""
CBT Agent Chat & Conversation Management Routes
"""

import time
from fastapi import APIRouter, Request
from backend.models.schemas import ChatPayload, ResetPayload, ChatEscalatePayload, ChatInterventionPayload
from backend.rate_limiter import check_rate_limit
from backend.session_manager import get_or_create_agent, sessions
from backend.chat_manager import chat_manager
from fastapi import WebSocket, WebSocketDisconnect

router = APIRouter(prefix="/api", tags=["chat"])

from fastapi.concurrency import run_in_threadpool

@router.post("/chat")
async def chat_api(payload: ChatPayload, request: Request):
    """Processes message via CBT ReAct agent with session context."""
    client_ip = request.client.host if request.client else "unknown"
    client_key = f"{client_ip}:{payload.session_id or 'anon'}"
    check_rate_limit(client_key)

    agent, sid, student_alias = get_or_create_agent(payload.session_id, payload.alias)
    
    if sid in sessions:
        sessions[sid].message_count += 1

    from agent.tools import COUNSELOR_ALERTS
    from backend.counselor_ws_manager import counselor_ws_manager
    len_before = len(COUNSELOR_ALERTS)

    reply = await run_in_threadpool(agent.chat, payload.message, session_id=sid, alias=student_alias)

    len_after = len(COUNSELOR_ALERTS)
    if len_after > len_before:
        for alert in COUNSELOR_ALERTS[len_before:len_after]:
            await counselor_ws_manager.send_to_counselors({"type": "new_alert", "alert": alert})

    return {
        "reply": reply,
        "session_id": sid,
        "alias": student_alias
    }

@router.post("/reset")
async def reset_api(payload: ResetPayload, request: Request):
    """Resets conversation history for current session."""
    client_ip = request.client.host if request.client else "unknown"
    client_key = f"{client_ip}:{payload.session_id or 'anon'}"
    check_rate_limit(client_key)

    if payload.session_id and payload.session_id in sessions:
        sessions[payload.session_id].agent.reset_session()
        sessions[payload.session_id].last_accessed = time.time()
        sessions[payload.session_id].message_count = 0
    
    return {"status": "success", "message": "Session reset"}

from agent.tools import COUNSELOR_ALERTS
import uuid

@router.post("/chat/escalate")
async def chat_escalate_api(payload: ChatEscalatePayload, request: Request):
    """Manually escalate to a counselor."""
    client_ip = request.client.host if request.client else "unknown"
    client_key = f"{client_ip}:{payload.session_id or 'anon'}"
    check_rate_limit(client_key)

    alert = {
        "id": str(uuid.uuid4()),
        "severity": "CRITICAL",
        "reason": f"Student {payload.alias} directly requested a {payload.mode.upper()} session with a counselor: {payload.reason}",
        "session_id": payload.session_id,
        "alias": payload.alias,
        "mode": payload.mode,
        "recommended_action": "Contact student immediately; dispatch on-call counselor.",
        "status": "PENDING",
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    }
    from backend.counselor_ws_manager import counselor_ws_manager
    COUNSELOR_ALERTS.append(alert)
    await counselor_ws_manager.send_to_counselors({"type": "new_alert", "alert": alert})
    return {"status": "success", "alert_id": alert["id"]}

@router.post("/chat/intervene")
async def chat_intervene_api(payload: ChatInterventionPayload, request: Request):
    """Counselor intervention in an active AI chat session."""
    if payload.session_id not in sessions:
        return {"status": "error", "message": "Session not found"}
        
    session = sessions[payload.session_id]
    
    # It's an AI session, so we can append to the agent's memory
    session.agent.add_message("assistant", f"[COUNSELOR INTERVENTION]: {payload.message}")
    
    # Push to student directly if they have a persistent WS connection
    from backend.counselor_ws_manager import counselor_ws_manager
    await counselor_ws_manager.send_to_student(payload.session_id, {
        "type": "counselor_message",
        "message": payload.message,
        "sender": "Counselor"
    })
    
    return {"status": "success"}

@router.websocket("/ws/counselor/intervene/p2p")
async def counselor_intervene_p2p_endpoint(websocket: WebSocket):
    """WebSocket endpoint for a counselor to join a P2P chat room."""
    room_id = websocket.query_params.get("room_id")
    await websocket.accept()
    if not room_id:
        await websocket.close(code=1008)
        return
        
    success = await chat_manager.counselor_join(websocket, room_id)
    if not success:
        await websocket.close(code=1008)
        return
        
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type == "chat_message":
                await chat_manager.relay_signal(websocket, data)
    except Exception:
        await chat_manager.disconnect(websocket)

@router.websocket("/ws/chat-room")
async def chat_room_endpoint(websocket: WebSocket):
    """WebSocket signaling endpoint for anonymous student-to-student text chat."""
    session_id = websocket.query_params.get("session_id", "anon-" + str(uuid.uuid4())[:8])
    alias = websocket.query_params.get("alias", "AnonPeer")
    await websocket.accept()
    await chat_manager.connect(websocket, session_id, alias)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type in ["chat_message"]:
                await chat_manager.relay_signal(websocket, data)
            elif msg_type == "next-peer":
                await chat_manager.connect(websocket, session_id, alias)
    except WebSocketDisconnect:
        await chat_manager.disconnect(websocket)
    except Exception:
        await chat_manager.disconnect(websocket)
