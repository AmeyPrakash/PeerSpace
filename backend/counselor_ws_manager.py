"""
PeerSpace Counselor WebSocket Manager
Handles persistent connections for students and counselors.
"""

import logging
import time
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger("peerspace.counselor_ws")

class CounselorWSManager:
    def __init__(self):
        # session_id -> list of WebSockets
        self.active_students: Dict[str, List[WebSocket]] = {}
        # counselor active sockets
        self.active_counselors: List[WebSocket] = []
        # msg_key -> timestamp for deduplication
        self._recent_messages: Dict[str, float] = {}

    def _is_duplicate_message(self, message: dict) -> bool:
        """Prevent duplicate student replies from being delivered to counselors."""
        if message.get("type") != "student_chat_reply":
            return False

        now = time.time()
        # Evict entries older than 20 seconds
        expired = [k for k, ts in self._recent_messages.items() if now - ts > 20.0]
        for k in expired:
            del self._recent_messages[k]

        msg_id = message.get("msg_id")
        if not msg_id:
            msg_id = f"{message.get('session_id')}:{message.get('message')}"

        if msg_id in self._recent_messages:
            logger.info("Suppressed duplicate student message to counselors: %s", msg_id)
            return True

        self._recent_messages[msg_id] = now
        return False

    async def connect_student(self, ws: WebSocket, session_id: str):
        if session_id not in self.active_students:
            self.active_students[session_id] = []
        self.active_students[session_id].append(ws)
        logger.info(f"Student {session_id} connected to persistent WS")

    async def disconnect_student(self, session_id: str, ws: WebSocket = None):
        if session_id in self.active_students:
            if ws and ws in self.active_students[session_id]:
                self.active_students[session_id].remove(ws)
            elif not ws:
                self.active_students[session_id].clear()
                
            if len(self.active_students[session_id]) == 0:
                del self.active_students[session_id]
            logger.info(f"Student {session_id} disconnected from persistent WS")

    async def connect_counselor(self, ws: WebSocket):
        self.active_counselors.append(ws)
        logger.info("Counselor connected to WS")

    async def disconnect_counselor(self, ws: WebSocket):
        if ws in self.active_counselors:
            self.active_counselors.remove(ws)
            logger.info("Counselor disconnected from WS")

    async def send_to_student(self, session_id: str, message: dict):
        if session_id in self.active_students:
            dead_sockets = []
            for ws in self.active_students[session_id]:
                try:
                    await ws.send_json(message)
                except Exception as e:
                    logger.error(f"Failed to send to student {session_id}: {e}")
                    dead_sockets.append(ws)
            
            for ws in dead_sockets:
                self.active_students[session_id].remove(ws)
            if len(self.active_students[session_id]) == 0:
                del self.active_students[session_id]

    async def send_to_counselors(self, message: dict):
        if self._is_duplicate_message(message):
            return

        dead_sockets = []
        for ws in self.active_counselors:
            try:
                await ws.send_json(message)
            except Exception:
                dead_sockets.append(ws)
        
        for ws in dead_sockets:
            self.active_counselors.remove(ws)

counselor_ws_manager = CounselorWSManager()
