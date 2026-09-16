"""
Counselor & Admin Portal Monitoring Routes
"""

import time
from fastapi import APIRouter, HTTPException, Depends, Header, status
from typing import Optional
from backend.models.schemas import AlertActionPayload
from backend.session_manager import sessions
from agent.tools import get_counselor_alerts, update_counselor_alert
from backend.config import COUNSELOR_PASSKEY_HASH
from backend.security import verify_passkey

router = APIRouter(prefix="/api/admin", tags=["admin"])

async def verify_admin(x_admin_token: Optional[str] = Header(None)):
    """Dependency to verify admin passkey."""
    if not x_admin_token or not verify_passkey(x_admin_token, COUNSELOR_PASSKEY_HASH):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing admin token"
        )
    return True

@router.get("/alerts", dependencies=[Depends(verify_admin)])
async def get_alerts_api():
    """Retrieves all professional intervention alerts sorted newest first."""
    alerts = get_counselor_alerts()
    return {
        "alerts": alerts,
        "total_alerts": len(alerts),
        "pending_count": sum(1 for a in alerts if a["status"] == "PENDING")
    }

@router.post("/alerts/{alert_id}/action", dependencies=[Depends(verify_admin)])
async def alert_action_api(alert_id: str, payload: AlertActionPayload):
    """Updates status of a counselor alert (DISPATCHED / RESOLVED)."""
    action = payload.action.upper()
    if action not in ["DISPATCHED", "RESOLVED"]:
        raise HTTPException(status_code=400, detail="Action must be DISPATCHED or RESOLVED.")
    
    updated = update_counselor_alert(alert_id, action)
    if not updated:
        raise HTTPException(status_code=404, detail="Alert not found.")
    
    return {"status": "success", "alert_id": alert_id, "new_status": action}

@router.get("/sessions", dependencies=[Depends(verify_admin)])
async def get_active_sessions():
    """Returns active anonymous student sessions."""
    now = time.time()
    active_list = []
    for sid, entry in reversed(sessions.items()):
        active_list.append({
            "session_id": sid[:8] + "...",
            "full_id": sid,
            "alias": entry.alias,
            "messages": entry.message_count,
            "last_active": f"{int((now - entry.last_accessed) / 60)}m ago" if (now - entry.last_accessed) > 60 else "Just now"
        })
    return {
        "active_sessions": active_list,
        "total_active": len(active_list)
    }

@router.get("/sessions/{session_id}/transcript", dependencies=[Depends(verify_admin)])
async def get_session_transcript(session_id: str):
    """Returns conversation transcript of an active student session for counselor context."""
    if session_id not in sessions:
        raise HTTPException(status_code=404, detail="Session not found.")
    
    session = sessions[session_id]
    history = []
    for msg in session.agent.conversation_history:
        role = msg.get("role")
        content = msg.get("content", "")
        if role == "system":
            continue
        
        clean_content = content
        sender = "Student"
        if role == "assistant":
            if "[COUNSELOR]:" in content:
                sender = "Counselor"
                clean_content = content.replace("[COUNSELOR]:", "").strip()
            elif "[COUNSELOR INTERVENTION]:" in content:
                sender = "Counselor"
                clean_content = content.replace("[COUNSELOR INTERVENTION]:", "").strip()
            elif "[COUNSELOR" in content:
                sender = "System"
                clean_content = content.strip()
            else:
                sender = "AI Coach"
                if "Final Answer:" in content:
                    clean_content = content.split("Final Answer:", 1)[1].strip()
        elif role == "user":
            sender = session.alias or "Student"

        history.append({
            "sender": sender,
            "role": role,
            "content": clean_content
        })

    return {
        "session_id": session_id,
        "alias": session.alias,
        "counselor_active": session.counselor_active,
        "transcript": history
    }

