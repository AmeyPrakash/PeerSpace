"""
CBT Agent Chat & Conversation Management Routes
"""

import time
from fastapi import APIRouter, Request
from backend.models.schemas import ChatPayload, ResetPayload
from backend.rate_limiter import check_rate_limit
from backend.session_manager import get_or_create_agent, sessions

router = APIRouter(prefix="/api", tags=["chat"])

@router.post("/chat")
async def chat_api(payload: ChatPayload, request: Request):
    """Processes message via CBT ReAct agent with session context."""
    client_ip = request.client.host if request.client else "unknown"
    client_key = f"{client_ip}:{payload.session_id or 'anon'}"
    check_rate_limit(client_key)

    agent, sid, student_alias = get_or_create_agent(payload.session_id, payload.alias)
    
    if sid in sessions:
        sessions[sid].message_count += 1

    reply = agent.chat(payload.message, session_id=sid, alias=student_alias)

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
