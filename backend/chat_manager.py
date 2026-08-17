"""
PeerSpace Text Chat Matchmaking Manager
Handles peer pairing and text message relay for anonymous student-to-student chat.
"""

import uuid
import logging
from typing import List, Dict
from fastapi import WebSocket

logger = logging.getLogger("peerspace.chat")

class ChatMatchmakingManager:
    def __init__(self):
        self.waiting_queue: List[dict] = []  # [{ "ws": WebSocket, "session_id": str, "alias": str }]
        self.active_rooms: Dict[str, dict] = {} # room_id -> { "peer1": {...}, "peer2": {...} }
        self.ws_to_room: Dict[WebSocket, str] = {}

    async def connect(self, ws: WebSocket, session_id: str, alias: str):
        await self.disconnect(ws)

        # Look for another waiting student
        matched_partner = None
        valid_queue = []
        for item in self.waiting_queue:
            if matched_partner is None and item["ws"] != ws and item["session_id"] != session_id:
                matched_partner = item
            else:
                valid_queue.append(item)
        self.waiting_queue = valid_queue

        if matched_partner:
            room_id = "textroom_" + uuid.uuid4().hex[:10]
            self.active_rooms[room_id] = {
                "peer1": matched_partner,
                "peer2": {"ws": ws, "session_id": session_id, "alias": alias}
            }
            self.ws_to_room[matched_partner["ws"]] = room_id
            self.ws_to_room[ws] = room_id

            logger.info("Text chat match created: Room %s between %s and %s", room_id, matched_partner['alias'], alias)

            # Notify initiator (peer 1)
            try:
                await matched_partner["ws"].send_json({
                    "type": "matched",
                    "room_id": room_id,
                    "peer_alias": alias,
                    "is_initiator": True
                })
            except Exception:
                pass

            # Notify receiver (peer 2)
            try:
                await ws.send_json({
                    "type": "matched",
                    "room_id": room_id,
                    "peer_alias": matched_partner["alias"],
                    "is_initiator": False
                })
            except Exception:
                pass
        else:
            self.waiting_queue.append({"ws": ws, "session_id": session_id, "alias": alias})
            try:
                await ws.send_json({
                    "type": "waiting",
                    "message": "Finding an anonymous campus peer..."
                })
            except Exception:
                pass

    async def relay_signal(self, ws: WebSocket, message: dict):
        room_id = self.ws_to_room.get(ws)
        if not room_id or room_id not in self.active_rooms:
            return

        room = self.active_rooms[room_id]
        target = room["peer2"] if room["peer1"]["ws"] == ws else room["peer1"]
        try:
            await target["ws"].send_json(message)
        except Exception:
            pass

    async def disconnect(self, ws: WebSocket):
        self.waiting_queue = [item for item in self.waiting_queue if item["ws"] != ws]

        room_id = self.ws_to_room.pop(ws, None)
        if room_id and room_id in self.active_rooms:
            room = self.active_rooms.pop(room_id, None)
            if room:
                other = room["peer2"] if room["peer1"]["ws"] == ws else room["peer1"]
                self.ws_to_room.pop(other["ws"], None)
                try:
                    await other["ws"].send_json({
                        "type": "peer_disconnected",
                        "message": "Your peer has disconnected from the chat."
                    })
                except Exception:
                    pass

chat_manager = ChatMatchmakingManager()
