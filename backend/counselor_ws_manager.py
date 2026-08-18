"""
PeerSpace Counselor WebSocket Manager
Handles persistent connections for students and counselors.
"""

import logging
from typing import Dict, List
from fastapi import WebSocket

logger = logging.getLogger("peerspace.counselor_ws")

class CounselorWSManager:
    def __init__(self):
        # session_id -> list of WebSockets
        self.active_students: Dict[str, List[WebSocket]] = {}
        # counselor active sockets
        self.active_counselors: List[WebSocket] = []

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
        dead_sockets = []
        for ws in self.active_counselors:
            try:
                await ws.send_json(message)
            except Exception:
                dead_sockets.append(ws)
        
        for ws in dead_sockets:
            self.active_counselors.remove(ws)

counselor_ws_manager = CounselorWSManager()
