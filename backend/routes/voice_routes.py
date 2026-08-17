"""
WebRTC Signaling & Voice Escalation Routes
"""

import time
import uuid
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from backend.models.schemas import VoiceEscalatePayload
from backend.voice_manager import voice_manager
from agent.tools import COUNSELOR_ALERTS

router = APIRouter(tags=["voice"])

@router.post("/api/voice/escalate")
async def voice_escalate_api(payload: VoiceEscalatePayload):
    """Triggers counselor escalation directly from a live student voice call."""
    alert = {
        "id": uuid.uuid4().hex[:8],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
        "session_id": payload.session_id,
        "alias": payload.alias,
        "severity": "HIGH",
        "reason": f"Voice Call Alert from {payload.alias} regarding peer {payload.peer_alias}: {payload.reason}",
        "recommended_action": "Contact student voice session; dispatch on-call counselor team.",
        "status": "PENDING"
    }
    COUNSELOR_ALERTS.insert(0, alert)
    return {"status": "success", "alert_id": alert["id"]}

@router.websocket("/ws/voice-room")
async def voice_room_endpoint(websocket: WebSocket):
    """WebSocket signaling endpoint for anonymous student-to-student WebRTC audio."""
    session_id = websocket.query_params.get("session_id", "anon-" + uuid.uuid4().hex[:8])
    alias = websocket.query_params.get("alias", "AnonPeer")
    await websocket.accept()
    await voice_manager.connect(websocket, session_id, alias)
    try:
        while True:
            data = await websocket.receive_json()
            msg_type = data.get("type")
            if msg_type in ["offer", "answer", "ice-candidate", "mute-status"]:
                await voice_manager.relay_signal(websocket, data)
            elif msg_type == "next-peer":
                await voice_manager.connect(websocket, session_id, alias)
    except WebSocketDisconnect:
        await voice_manager.disconnect(websocket)
    except Exception:
        await voice_manager.disconnect(websocket)
