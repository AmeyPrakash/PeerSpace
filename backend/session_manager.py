"""
PeerSpace Session & Anonymous Identity Manager
"""

import time
import uuid
import re
import random
from collections import OrderedDict
from typing import Optional, Tuple
from agent.agent import PeerSpaceAgent

SESSION_EXPIRY_SECONDS = 3600
MAX_ACTIVE_SESSIONS = 500

class SessionEntry:
    def __init__(self, agent: PeerSpaceAgent, alias: str):
        self.agent = agent
        self.alias = alias
        self.last_accessed = time.time()
        self.message_count = 0

sessions: OrderedDict[str, SessionEntry] = OrderedDict()

ADJECTIVES = ["Mindful", "Quiet", "Calm", "Gentle", "Resilient", "Brave", "Kind", "Sage", "Patient", "Hopeful", "Warm", "Bright"]
NOUNS = ["Sparrow", "Comet", "River", "Falcon", "Otter", "Cedar", "Breeze", "Clover", "Haven", "Beacon", "Panda", "Willow"]

def generate_anonymous_alias() -> str:
    """Generates an anonymous university pseudonym."""
    return f"{random.choice(ADJECTIVES)}{random.choice(NOUNS)}{random.randint(10, 99)}"

def get_or_create_agent(session_id: Optional[str] = None, alias: Optional[str] = None, randomize_alias: bool = False) -> Tuple[PeerSpaceAgent, str, str]:
    """Retrieves an existing agent session or initializes a new anonymous identity."""
    now = time.time()
    
    # Prune expired sessions
    expired_keys = [sid for sid, s in sessions.items() if now - s.last_accessed > SESSION_EXPIRY_SECONDS]
    for sid in expired_keys:
        sessions.pop(sid, None)

    # Evict oldest if full
    if len(sessions) >= MAX_ACTIVE_SESSIONS:
        sessions.popitem(last=False)

    if not session_id or session_id not in sessions:
        sid = session_id if (session_id and re.match(r"^[a-zA-Z0-9_-]{1,64}$", session_id)) else str(uuid.uuid4())
        student_alias = alias if (alias and not randomize_alias) else generate_anonymous_alias()
        new_agent = PeerSpaceAgent()
        sessions[sid] = SessionEntry(new_agent, student_alias)
        return new_agent, sid, student_alias
    else:
        entry = sessions[session_id]
        entry.last_accessed = now
        sessions.move_to_end(session_id)
        if randomize_alias:
            new_alias = generate_anonymous_alias()
            while new_alias == entry.alias:
                new_alias = generate_anonymous_alias()
            entry.alias = new_alias
        elif alias and alias != entry.alias:
            entry.alias = alias
        return entry.agent, session_id, entry.alias
